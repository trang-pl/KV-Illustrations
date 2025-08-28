"""
Figma Plugin API Client
Tích hợp với Figma Plugin API để có thêm thông tin và capabilities
"""

import asyncio
import json
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .figma_sync import FigmaAPIClient
from ..utils.node_id_converter import NodeIdConverter, FigmaNodeResolver


@dataclass
class PluginNodeInfo:
    """Thông tin node từ Plugin API"""
    id: str
    name: str
    type: str
    parent_id: Optional[str] = None
    children_count: int = 0
    bounds: Optional[Dict] = None
    fills: Optional[List] = None
    strokes: Optional[List] = None
    effects: Optional[List] = None
    export_settings: Optional[List] = None
    plugin_data: Optional[Dict] = None


class FigmaPluginClient:
    """Client để giao tiếp với Figma Plugin API"""

    def __init__(self, token: str, plugin_id: Optional[str] = None):
        self.token = token
        self.plugin_id = plugin_id
        self.base_url = "https://api.figma.com/v1"
        self.plugin_base_url = "https://api.figma.com/v1/plugins"
        self.headers = {"X-Figma-Token": token, "Content-Type": "application/json"}

        # Fallback to REST API client
        self.rest_client = FigmaAPIClient(token)
        self.node_resolver = FigmaNodeResolver(self.rest_client)

    async def get_plugin_manifest(self, plugin_id: str) -> Optional[Dict]:
        """Lấy manifest của plugin"""
        url = f"{self.plugin_base_url}/{plugin_id}/manifest"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Failed to get plugin manifest: {response.status}")
                        return None
            except Exception as e:
                print(f"Error getting plugin manifest: {e}")
                return None

    async def run_plugin_command(
        self,
        file_key: str,
        node_id: str,
        command: str,
        parameters: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Chạy plugin command trên một node"""

        if not self.plugin_id:
            print("No plugin ID configured")
            return None

        url = f"{self.base_url}/files/{file_key}/plugin/{self.plugin_id}/run"
        payload = {
            "node_id": node_id,
            "command": command,
            "parameters": parameters or {}
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Plugin command failed: {response.status}")
                        error_text = await response.text()
                        print(f"Error: {error_text}")
                        return None
            except Exception as e:
                print(f"Error running plugin command: {e}")
                return None

    async def get_node_plugin_data(self, file_key: str, node_id: str) -> Optional[Dict]:
        """Lấy plugin data của node"""
        command_result = await self.run_plugin_command(
            file_key=file_key,
            node_id=node_id,
            command="getPluginData",
            parameters={}
        )

        if command_result and "data" in command_result:
            return command_result["data"]

        return None

    async def get_node_with_plugin_enhancement(
        self,
        file_key: str,
        node_id: str
    ) -> Optional[PluginNodeInfo]:
        """Lấy thông tin node với plugin enhancement"""

        # First try to resolve node with fallback
        resolved_node = await self.node_resolver.resolve_node_with_fallbacks(file_key, node_id)

        if not resolved_node:
            return None

        node_data = resolved_node["node_data"]
        resolved_id = resolved_node["resolved_id"]

        # Try to get plugin data
        plugin_data = None
        if self.plugin_id:
            plugin_data = await self.get_node_plugin_data(file_key, resolved_id)

        # Convert to PluginNodeInfo
        bounds = node_data.get("absoluteBoundingBox", {})

        plugin_node = PluginNodeInfo(
            id=resolved_id,
            name=node_data.get("name", "Unknown"),
            type=node_data.get("type", "Unknown"),
            parent_id=node_data.get("parent", {}).get("id") if node_data.get("parent") else None,
            children_count=len(node_data.get("children", [])),
            bounds=bounds if bounds else None,
            fills=node_data.get("fills", []),
            strokes=node_data.get("strokes", []),
            effects=node_data.get("effects", []),
            export_settings=node_data.get("exportSettings", []),
            plugin_data=plugin_data
        )

        return plugin_node

    async def batch_get_nodes_with_plugin_data(
        self,
        file_key: str,
        node_ids: List[str],
        batch_size: int = 5
    ) -> Dict[str, PluginNodeInfo]:
        """Batch get nodes với plugin data"""

        results = {}

        # Process in batches
        for i in range(0, len(node_ids), batch_size):
            batch = node_ids[i:i + batch_size]

            tasks = []
            for node_id in batch:
                task = self.get_node_with_plugin_enhancement(file_key, node_id)
                tasks.append(task)

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for node_id, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    print(f"Error getting node {node_id}: {result}")
                elif result:
                    results[node_id] = result

            # Rate limiting
            if i + batch_size < len(node_ids):
                await asyncio.sleep(1.0)

        return results

    async def find_nodes_by_plugin_criteria(
        self,
        file_key: str,
        criteria: Dict[str, Any]
    ) -> List[PluginNodeInfo]:
        """Tìm nodes dựa trên plugin criteria"""

        # Get root structure
        root_result = await self.node_resolver.resolve_node_with_fallbacks(file_key, "0:1")
        if not root_result:
            return []

        root_node = root_result["node_data"]

        def matches_criteria(node_data: Dict) -> bool:
            """Check if node matches search criteria"""
            for key, value in criteria.items():
                if key == "type" and node_data.get("type") != value:
                    return False
                elif key == "name_contains":
                    if value.lower() not in node_data.get("name", "").lower():
                        return False
                elif key == "has_plugin_data" and not node_data.get("pluginData"):
                    return False
                elif key == "min_width":
                    bounds = node_data.get("absoluteBoundingBox", {})
                    if bounds.get("width", 0) < value:
                        return False
                elif key == "min_height":
                    bounds = node_data.get("absoluteBoundingBox", {})
                    if bounds.get("height", 0) < value:
                        return False

            return True

        def search_nodes(node: Dict) -> List[PluginNodeInfo]:
            results = []

            if matches_criteria(node):
                # Convert to PluginNodeInfo
                plugin_node = PluginNodeInfo(
                    id=node.get("id", ""),
                    name=node.get("name", "Unknown"),
                    type=node.get("type", "Unknown"),
                    children_count=len(node.get("children", [])),
                    bounds=node.get("absoluteBoundingBox"),
                    fills=node.get("fills", []),
                    strokes=node.get("strokes", []),
                    effects=node.get("effects", []),
                    export_settings=node.get("exportSettings", [])
                )
                results.append(plugin_node)

            # Search in children
            for child in node.get("children", []):
                results.extend(search_nodes(child))

            return results

        return search_nodes(root_node)

    async def export_with_plugin_enhancement(
        self,
        file_key: str,
        node_ids: List[str],
        format: str = "svg"
    ) -> Dict[str, str]:
        """Export với plugin enhancement"""

        # First try plugin-enhanced export
        if self.plugin_id:
            plugin_export_result = await self.run_plugin_command(
                file_key=file_key,
                node_id=node_ids[0] if node_ids else "0:1",  # Use first node or root
                command="exportNodes",
                parameters={
                    "node_ids": node_ids,
                    "format": format,
                    "scale": 1
                }
            )

            if plugin_export_result and "urls" in plugin_export_result:
                return plugin_export_result["urls"]

        # Fallback to REST API export
        return await self.rest_client.export_svg_batch(file_key, node_ids)


class EnhancedFigmaSyncService:
    """Enhanced Figma Sync Service với Plugin API integration"""

    def __init__(self, plugin_id: Optional[str] = None):
        import os
        token = os.environ.get('FIGMA_API_TOKEN')
        if not token:
            raise ValueError("FIGMA_API_TOKEN environment variable is not set")

        self.plugin_client = FigmaPluginClient(token, plugin_id)
        self.node_converter = NodeIdConverter()

    async def enhanced_process_sync(
        self,
        file_key: str,
        node_id: str,
        output_dir: str,
        force_sync: bool = False,
        use_plugin_enhancement: bool = True
    ) -> Dict[str, Any]:
        """Enhanced sync process với plugin integration"""

        print("Enhanced Figma Sync với Plugin Integration v2.0")
        print("=" * 60)

        # Step 1: Resolve node với multiple fallbacks
        print(f"Step 1: Resolving node {node_id}...")
        resolved_node = await self.plugin_client.node_resolver.resolve_node_with_fallbacks(
            file_key, node_id
        )

        if not resolved_node:
            return {"error": f"Could not resolve node {node_id}"}

        actual_node_id = resolved_node["resolved_id"]
        node_data = resolved_node["node_data"]

        print(f"✓ Node resolved: {actual_node_id} ({node_data.get('name', 'Unknown')})")

        # Step 2: Get plugin-enhanced node info
        if use_plugin_enhancement:
            print("Step 2: Getting plugin-enhanced node info...")
            plugin_node_info = await self.plugin_client.get_node_with_plugin_enhancement(
                file_key, actual_node_id
            )

            if plugin_node_info:
                print(f"✓ Plugin data retrieved for {plugin_node_info.name}")
                print(f"  - Type: {plugin_node_info.type}")
                print(f"  - Children: {plugin_node_info.children_count}")
                if plugin_node_info.bounds:
                    print(f"  - Size: {plugin_node_info.bounds.get('width', 0)}x{plugin_node_info.bounds.get('height', 0)}")

        # Step 3: Find exportable children
        print("Step 3: Finding exportable children...")
        exportable_children = self.plugin_client.rest_client.find_exportable_children(node_data)

        print(f"✓ Found {len(exportable_children)} exportable children")

        # Step 4: Enhanced export
        print("Step 4: Enhanced export process...")

        if not exportable_children:
            return {"message": "No exportable children found"}

        # Get node IDs for export
        node_ids_to_export = [child["id"] for child in exportable_children]

        # Use plugin-enhanced export if available
        export_urls = await self.plugin_client.export_with_plugin_enhancement(
            file_key, node_ids_to_export
        )

        print(f"✓ Got {len(export_urls)} export URLs")

        # Step 5: Download and save
        print("Step 5: Downloading and saving files...")

        import aiofiles
        from pathlib import Path

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        successful_downloads = 0

        for child in exportable_children:
            node_id = child["id"]
            if node_id in export_urls:
                url = export_urls[node_id]

                # Create filename
                safe_name = self.plugin_client.rest_client.sanitize_filename(child["name"])
                filename = f"enhanced_{safe_name}_{node_id.replace(':', '_')}.svg"
                filepath = output_path / filename

                # Download
                svg_content = await self.plugin_client.rest_client.download_svg_content(url)

                if svg_content:
                    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                        await f.write(svg_content)

                    successful_downloads += 1
                    print(f"✓ Saved: {filename}")

        # Summary
        print("\n" + "="*50)
        print("ENHANCED SYNC SUMMARY")
        print("="*50)
        print(f"Original node ID: {node_id}")
        print(f"Resolved node ID: {actual_node_id}")
        print(f"Exportable children: {len(exportable_children)}")
        print(f"Successful downloads: {successful_downloads}")
        print(f"Output directory: {output_path.absolute()}")

        return {
            "original_node_id": node_id,
            "resolved_node_id": actual_node_id,
            "exportable_children_count": len(exportable_children),
            "successful_downloads": successful_downloads,
            "output_dir": str(output_path),
            "plugin_enhanced": use_plugin_enhancement and plugin_node_info is not None
        }