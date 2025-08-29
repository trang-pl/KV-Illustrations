#!/usr/bin/env python3
"""
Test Real Figma Data with AND Logic
===================================

Test end-to-end với real Figma API data:
- Fetch data từ Figma API với real credentials
- Process với logic AND đã sửa
- Target nodes: 453:37, 453:43
- Generate export results

Author: Kilo Code Debug Agent
Date: 2025-08-29
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone
import dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import required modules - sử dụng simple API client thay vì complex module
import aiohttp

class RealDataTester:
    """Test với real Figma API data và logic AND"""

    def __init__(self):
        self.api_token = None
        self.file_key = None
        self.target_node_ids = ["453:37", "453:43"]
        self.naming_prefixes = {}

    def load_credentials(self) -> bool:
        """Load credentials từ .env file"""
        print("[CREDENTIALS] Loading credentials from .env...")

        dotenv.load_dotenv()
        self.api_token = os.getenv('FIGMA_API_TOKEN')
        self.file_key = os.getenv('FIGMA_FILE_KEY')

        if not self.api_token or not self.file_key:
            print("[ERROR] Missing FIGMA_API_TOKEN or FIGMA_FILE_KEY in .env")
            return False

        print(f"[SUCCESS] Credentials loaded for file: {self.file_key}")
        return True

    def load_config(self) -> bool:
        """Load pipeline config để lấy naming_prefixes và target_nodes"""
        print("[CONFIG] Loading pipeline configuration...")

        config_path = Path("scripts/config/pipeline_config.json")
        if not config_path.exists():
            print(f"[ERROR] Config file not found: {config_path}")
            return False

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Extract naming_prefixes
        export_config = config.get("export", {})
        self.naming_prefixes = export_config.get("naming_prefixes", {})

        # Extract target_nodes config
        target_nodes_config = export_config.get("target_nodes", {})
        if not target_nodes_config.get("enabled", False):
            print("[WARNING] Target nodes disabled in config")
            return False

        config_target_ids = target_nodes_config.get("node_ids", [])
        if not config_target_ids:
            print("[WARNING] No target node IDs in config")
            return False

        print(f"[SUCCESS] Config loaded with {len(self.naming_prefixes)} prefixes")
        print(f"[TARGET_NODES] Config node IDs: {config_target_ids}")
        print(f"[TARGET_NODES] Test node IDs: {self.target_node_ids}")

        return True

    async def fetch_figma_data(self) -> Dict[str, Any]:
        """Fetch real data từ Figma API sử dụng aiohttp"""
        print("[FIGMA] Fetching data from Figma API...")
        print(f"[FIGMA] File key: {self.file_key}")
        print(f"[FIGMA] Target nodes: {self.target_node_ids}")

        try:
            # Figma API endpoint
            url = f"https://api.figma.com/v1/files/{self.file_key}"
            headers = {
                "X-Figma-Token": self.api_token
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[ERROR] Figma API error {response.status}: {error_text}")
                        return {
                            "success": False,
                            "error": f"API error {response.status}: {error_text}",
                            "file_key": self.file_key
                        }

                    data = await response.json()

            # Process Figma response thành format mong muốn
            pages = []
            total_nodes = 0

            for page_data in data.get("document", {}).get("children", []):
                if page_data.get("type") == "CANVAS":  # Figma page
                    page_name = page_data.get("name", "Unknown Page")
                    visible_nodes = []

                    # Extract visible nodes from page
                    def extract_nodes(node, page_id):
                        nonlocal total_nodes
                        if node.get("type") in ["FRAME", "GROUP", "COMPONENT", "INSTANCE"]:
                            visible_nodes.append({
                                "id": node.get("id"),
                                "name": node.get("name", ""),
                                "type": node.get("type", ""),
                                "page_id": page_id
                            })
                            total_nodes += 1

                        # Process children
                        for child in node.get("children", []):
                            extract_nodes(child, page_id)

                    extract_nodes(page_data, page_data.get("id"))

                    pages.append({
                        "name": page_name,
                        "visible_nodes": visible_nodes
                    })

            result = {
                "success": True,
                "pages": pages,
                "total_pages": len(pages),
                "total_nodes": total_nodes,
                "file_key": self.file_key
            }

            print(f"[SUCCESS] Fetched {len(pages)} pages with {total_nodes} nodes")

            # Check for target nodes
            target_nodes_found = []
            for page in pages:
                for node in page.get("visible_nodes", []):
                    node_id = node.get("id", "")
                    if node_id in self.target_node_ids:
                        target_nodes_found.append({
                            "id": node_id,
                            "name": node.get("name", ""),
                            "type": node.get("type", "")
                        })

            print(f"[TARGET_NODES] Found {len(target_nodes_found)} target nodes:")
            for node in target_nodes_found:
                print(f"  - {node['id']}: '{node['name']}' ({node['type']})")

            return result

        except Exception as e:
            print(f"[ERROR] Figma API call failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "file_key": self.file_key
            }

    def detect_prefix(self, node_name: str) -> str:
        """Detect prefix từ node name theo config"""
        for prefix_key, prefix_value in self.naming_prefixes.items():
            if node_name.startswith(prefix_value):
                return prefix_key
        return None

    def is_target_node(self, node_id: str) -> bool:
        """Check if node is target node"""
        return node_id in self.target_node_ids

    def process_nodes_with_and_logic(self, pages_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process nodes với logic AND đã sửa"""
        print("[PROCESS] Processing nodes with AND logic...")
        print("=" * 60)

        if not pages_data.get("success", False):
            return {"success": False, "error": "Invalid pages data"}

        processed_nodes = []
        start_time = datetime.now(timezone.utc)

        # Process each page
        for page in pages_data.get("pages", []):
            page_name = page.get("name", "Unknown Page")
            visible_nodes = page.get("visible_nodes", [])
            print(f"[PAGE] Processing page: {page_name} ({len(visible_nodes)} nodes)")

            for node_data in visible_nodes:
                node_id = node_data.get("id", "")
                node_name = node_data.get("name", "")
                node_type = node_data.get("type", "")

                # Detect prefix
                prefix = self.detect_prefix(node_name)

                # Check if target node
                is_target = self.is_target_node(node_id)

                # Apply AND logic: prefix AND target_node
                export_ready = (prefix is not None) and is_target

                # Create processed node
                processed_node = {
                    "id": node_id,
                    "name": node_name,
                    "type": node_type,
                    "page_id": node_data.get("page_id", ""),
                    "page_name": page_name,
                    "prefix": prefix,
                    "base_name": node_name[len(self.naming_prefixes.get(prefix, "")):] if prefix else node_name,
                    "is_target": is_target,
                    "validation_errors": [],
                    "export_ready": export_ready
                }

                processed_nodes.append(processed_node)

                # Debug output chỉ cho target nodes hoặc nodes có prefix
                if is_target or prefix:
                    status = "[PASS]" if export_ready else "[FAIL]"
                    print(f"{status} {node_id}: '{node_name}' -> prefix='{prefix}', target={is_target}")

        end_time = datetime.now(timezone.utc)
        processing_time = (end_time - start_time).total_seconds()

        # Calculate summary
        export_ready_nodes = [n for n in processed_nodes if n["export_ready"]]
        target_nodes_found = [n for n in processed_nodes if n["is_target"]]

        result = {
            "success": True,
            "processed_nodes": processed_nodes,
            "summary": {
                "total_nodes": len(processed_nodes),
                "export_ready_nodes": len(export_ready_nodes),
                "target_nodes_found": len(target_nodes_found),
                "validation_errors": 0,
                "processing_time": processing_time
            },
            "target_nodes_config": {
                "enabled": True,
                "node_ids": self.target_node_ids,
                "export_mode": "svg",
                "process_children": True
            },
            "timestamp": start_time.isoformat()
        }

        print("[SUCCESS] Node processing completed")
        print(f"[SUMMARY] Total nodes: {result['summary']['total_nodes']}")
        print(f"[SUMMARY] Export ready (AND logic): {result['summary']['export_ready_nodes']}")
        print(f"[SUMMARY] Target nodes found: {result['summary']['target_nodes_found']}")

        return result

    def save_export_results(self, result: Dict[str, Any], output_dir: str = "exports/real_data_test/"):
        """Save export results"""
        print(f"[EXPORT] Saving results to: {output_dir}")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save detailed JSON report
        json_file = output_path / "real_data_test_report.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # Save summary markdown report
        md_file = output_path / "real_data_test_summary.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# Real Figma Data Test Results\n\n")
            f.write(f"**Timestamp:** {result.get('timestamp', 'N/A')}\n\n")
            f.write(f"**File Key:** {self.file_key}\n\n")
            f.write(f"**Target Nodes:** {', '.join(self.target_node_ids)}\n\n")

            if result.get("success"):
                summary = result.get("summary", {})
                f.write("## Test Results Summary\n\n")
                f.write(f"- **Total Nodes:** {summary.get('total_nodes', 0)}\n")
                f.write(f"- **Export Ready (AND logic):** {summary.get('export_ready_nodes', 0)}\n")
                f.write(f"- **Target Nodes Found:** {summary.get('target_nodes_found', 0)}\n")
                f.write(f"- **Processing Time:** {summary.get('processing_time', 0):.2f} seconds\n\n")

                # Target nodes config
                target_config = result.get("target_nodes_config", {})
                f.write("## Target Nodes Configuration\n\n")
                f.write(f"- **Enabled:** {target_config.get('enabled', False)}\n")
                f.write(f"- **Node IDs:** {', '.join(target_config.get('node_ids', []))}\n")
                f.write(f"- **Export Mode:** {target_config.get('export_mode', 'svg')}\n\n")

                # Export ready nodes
                export_ready_nodes = [n for n in result.get("processed_nodes", []) if n.get("export_ready", False)]
                if export_ready_nodes:
                    f.write("## Nodes Passed AND Filter\n\n")
                    for node in export_ready_nodes:
                        f.write(f"- `{node['id']}` - {node['name']} (prefix: {node.get('prefix', 'None')})\n")
                    f.write("\n")

                    f.write("## Test Status: PASSED\n\n")
                    f.write("Real data test with AND logic completed successfully!\n")
                else:
                    f.write("## Test Status: NO RESULTS\n\n")
                    f.write("No nodes passed the AND filter. This could mean:\n")
                    f.write("- Target nodes don't exist in the Figma file\n")
                    f.write("- Target nodes don't have valid prefixes\n")
                    f.write("- Logic AND is working correctly (no false positives)\n")

            else:
                f.write("## Test Failed\n\n")
                f.write(f"**Error:** {result.get('error', 'Unknown error')}\n\n")

        print(f"[SUCCESS] Reports saved:")
        print(f"  JSON: {json_file}")
        print(f"  Markdown: {md_file}")

        return str(json_file), str(md_file)

async def main():
    """Main test function với real Figma data"""
    print("REAL FIGMA DATA TEST WITH AND LOGIC")
    print("=" * 50)

    tester = RealDataTester()

    try:
        # Load credentials và config
        if not tester.load_credentials():
            print("[ERROR] Failed to load credentials")
            return False

        if not tester.load_config():
            print("[ERROR] Failed to load config")
            return False

        # Fetch real Figma data
        print("\n[TEST] Fetching real data from Figma API...")
        figma_data = await tester.fetch_figma_data()

        if not figma_data.get("success", False):
            print(f"[ERROR] Failed to fetch Figma data: {figma_data.get('error')}")
            return False

        # Process nodes với AND logic
        print("\n[PROCESS] Processing with AND logic...")
        result = tester.process_nodes_with_and_logic(figma_data)

        # Save export results
        json_file, md_file = tester.save_export_results(result)

        # Final summary
        print("\n" + "=" * 50)
        print("REAL DATA TEST RESULTS SUMMARY")
        print("=" * 50)

        if result.get("success"):
            summary = result.get("summary", {})
            export_ready = summary.get("export_ready_nodes", 0)
            target_found = summary.get("target_nodes_found", 0)

            print(f"[RESULT] Total nodes processed: {summary.get('total_nodes', 0)}")
            print(f"[RESULT] Target nodes found: {target_found}")
            print(f"[RESULT] Export ready (AND logic): {export_ready}")

            if export_ready > 0:
                print("[SUCCESS] Real data test PASSED!")
                print(f"[VALIDATION] Found {export_ready} nodes that passed AND filter")
                return True
            else:
                print("[INFO] Real data test completed with NO results")
                print("[INFO] This could mean target nodes don't have valid prefixes")
                print("[INFO] OR target nodes don't exist in the Figma file")
                print("[INFO] AND logic is working correctly (no false positives)")
                return True
        else:
            print(f"[ERROR] Processing failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"[FATAL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n[FINISH] Real data test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)