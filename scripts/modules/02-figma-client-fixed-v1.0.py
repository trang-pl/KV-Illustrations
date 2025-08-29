#!/usr/bin/env python3
"""
Figma Client Module v1.0 - MODULAR ARCHITECTURE
==============================================

Refactored Figma API client with modular architecture and config management.
Uses separate modules for config, filtering, API client, and report generation.

Features:
- Modular architecture with separate concerns
- Configuration-driven behavior
- Comprehensive error handling
- Rate limiting and throttling
- Unicode-safe operations

Author: Kilo Code Debug Agent
Version: 1.0.2 (Modular)
Date: 2025-08-29
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import modular components using importlib
import importlib.util
import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import config_manager module
config_spec = importlib.util.spec_from_file_location("config_manager", current_dir / "02-config-manager.py")
config_manager = importlib.util.module_from_spec(config_spec)
config_spec.loader.exec_module(config_manager)
ConfigManager = config_manager.ConfigManager
load_config = config_manager.load_config

# Import api_client module
api_spec = importlib.util.spec_from_file_location("api_client", current_dir / "02-api-client.py")
api_client = importlib.util.module_from_spec(api_spec)
api_spec.loader.exec_module(api_client)
FigmaApiClient = api_client.FigmaApiClient

# Import filter_engine module
filter_spec = importlib.util.spec_from_file_location("filter_engine", current_dir / "02-filter-engine.py")
filter_engine = importlib.util.module_from_spec(filter_spec)
filter_spec.loader.exec_module(filter_engine)
FilterEngine = filter_engine.FilterEngine

# Import report_generator module
report_spec = importlib.util.spec_from_file_location("report_generator", current_dir / "02-report-generator.py")
report_generator = importlib.util.module_from_spec(report_spec)
report_spec.loader.exec_module(report_generator)
ReportGenerator = report_generator.ReportGenerator

class FigmaClientOrchestrator:
    """Orchestrator for Figma client operations using modular components"""

    def __init__(self, api_token: str, config_path: Optional[str] = None):
        """
        Initialize Figma client orchestrator

        Args:
            api_token: Figma API token
            config_path: Path to configuration file
        """
        self.api_token = api_token
        self.config_path = config_path

        # Initialize components
        self.config_manager = ConfigManager(config_path)
        self.api_client = FigmaApiClient(api_token, self.config_manager)
        self.filter_engine = FilterEngine(self.config_manager)
        self.report_generator = ReportGenerator(self.config_manager)

        print(f"[DEBUG] [ORCHESTRATOR] FigmaClientOrchestrator initialized")
        print(f"[DEBUG] [ORCHESTRATOR] Config path: {self.config_manager.config_path}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.api_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.api_client.__aexit__(exc_type, exc_val, exc_tb)

    async def process_file(self, file_key: str, custom_filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process Figma file with full pipeline: fetch -> filter -> report

        Args:
            file_key: Figma file key
            custom_filters: Custom filter parameters (optional)

        Returns:
            Dict containing processing results
        """
        print(f"[DEBUG] [ORCHESTRATOR] Processing file: {file_key}")

        try:
            # Step 1: Fetch file pages
            print("[DEBUG] [ORCHESTRATOR] Step 1: Fetching file pages...")
            pages_result = await self.api_client.fetch_file_pages(file_key)

            if not pages_result["success"]:
                print(f"[DEBUG] [ORCHESTRATOR] Failed to fetch pages: {pages_result.get('error')}")
                return pages_result

            # Step 1.5: Process target nodes if enabled
            print("[DEBUG] [ORCHESTRATOR] Step 1.5: Processing target nodes...")
            pages_result = await self._process_target_nodes(file_key, pages_result)

            # Step 2: Apply filtering
            print("[DEBUG] [ORCHESTRATOR] Step 2: Applying filters...")
            filter_result = await self._apply_filters(pages_result, custom_filters)

            # Step 3: Generate reports
            print("[DEBUG] [ORCHESTRATOR] Step 3: Generating reports...")
            await self._generate_reports(filter_result)

            print("[DEBUG] [ORCHESTRATOR] Processing completed successfully")
            return filter_result

        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            print(f"[DEBUG] [ORCHESTRATOR] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "file_key": file_key
            }

    async def _apply_filters(self, pages_result: Dict[str, Any], custom_filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Apply filtering to pages result

        Args:
            pages_result: Raw pages data
            custom_filters: Custom filter parameters

        Returns:
            Filtered result
        """
        if custom_filters:
            # Use custom filters
            include_patterns = custom_filters.get("include_patterns")
            exclude_patterns = custom_filters.get("exclude_patterns")
            case_sensitive = custom_filters.get("case_sensitive")
        else:
            # Use config defaults
            include_patterns = None  # Will use config defaults
            exclude_patterns = None  # Will use config defaults
            case_sensitive = None    # Will use config defaults

        filter_result = self.filter_engine.filter_nodes_by_criteria(
            pages_result,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            case_sensitive=case_sensitive
        )

        # Convert FilterResult to dict for consistency
        return {
            "success": filter_result.success,
            "pages": filter_result.pages,
            "total_pages": filter_result.total_pages,
            "total_nodes": filter_result.total_nodes,
            "filter_criteria": filter_result.filter_criteria,
            "error": filter_result.error
        }

    async def _generate_reports(self, result: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generate reports from processing result

        Args:
            result: Processing result

        Returns:
            Tuple of (json_report_path, markdown_report_path)
        """
        # Get output directory from config
        output_settings = self.config_manager.get_output_settings()
        output_dir = output_settings.default_output_dir

        # Generate reports
        json_report, markdown_report = self.report_generator.generate_reports(result, output_dir)

        print(f"[DEBUG] [ORCHESTRATOR] Reports generated:")
        print(f"[DEBUG] [ORCHESTRATOR]   JSON: {json_report}")
        print(f"[DEBUG] [ORCHESTRATOR]   Markdown: {markdown_report}")

        return json_report, markdown_report

    async def _process_target_nodes(self, file_key: str, pages_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process target nodes if enabled in config

        Args:
            file_key: Figma file key
            pages_result: Current pages result

        Returns:
            Updated pages result with target node data
        """
        try:
            # Load target_nodes config
            config = self._load_target_nodes_config()
            if not config or not config.get("enabled", False):
                print("[DEBUG] [TARGET_NODES] Target nodes disabled or not configured")
                return pages_result

            target_node_ids = config.get("node_ids", [])
            export_mode = config.get("export_mode", "svg")
            process_children = config.get("process_children", True)

            print(f"[DEBUG] [TARGET_NODES] Processing {len(target_node_ids)} target nodes")
            print(f"[DEBUG] [TARGET_NODES] Export mode: {export_mode}")
            print(f"[DEBUG] [TARGET_NODES] Process children: {process_children}")

            if not target_node_ids:
                print("[DEBUG] [TARGET_NODES] No target node IDs specified")
                return pages_result

            # Fetch detailed data for target nodes
            target_nodes_data = await self._fetch_target_nodes_data(file_key, target_node_ids)

            # Enhance pages_result with target node data
            enhanced_result = pages_result.copy()
            enhanced_result["target_nodes"] = target_nodes_data
            enhanced_result["target_nodes_config"] = config

            print(f"[DEBUG] [TARGET_NODES] Successfully processed {len(target_nodes_data)} target nodes")
            return enhanced_result

        except Exception as e:
            print(f"[DEBUG] [TARGET_NODES] Error processing target nodes: {str(e)}")
            # Return original result if target nodes processing fails
            return pages_result

    def _load_target_nodes_config(self) -> Optional[Dict[str, Any]]:
        """Load target_nodes configuration from figma_client config"""
        try:
            # Use config_manager to get target_nodes config
            if self.config_manager:
                target_nodes = self.config_manager.get_target_nodes()
                return {
                    "enabled": target_nodes.enabled,
                    "node_ids": target_nodes.node_ids,
                    "export_mode": target_nodes.export_mode,
                    "process_children": target_nodes.process_children
                }

            # Fallback: Load config directly from file
            import json
            config_path = Path(__file__).parent.parent / "config" / "figma_client_config.json"

            if not config_path.exists():
                print(f"[DEBUG] [TARGET_NODES] Config file not found: {config_path}")
                return None

            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            target_nodes_config = config.get("target_nodes", {})
            return target_nodes_config

        except Exception as e:
            print(f"[DEBUG] [TARGET_NODES] Error loading config: {str(e)}")
            return None

    async def _fetch_target_nodes_data(self, file_key: str, node_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch detailed data for target nodes

        Args:
            file_key: Figma file key
            node_ids: List of node IDs to fetch

        Returns:
            List of node data dictionaries
        """
        target_nodes_data = []

        for node_id in node_ids:
            try:
                print(f"[DEBUG] [TARGET_NODES] Fetching data for node: {node_id}")

                # Use api_client to fetch individual node data
                # Note: This assumes api_client has a method to fetch individual nodes
                # If not, we'll need to implement it or use the existing fetch_file_pages data
                node_data = await self._get_node_data(file_key, node_id)

                if node_data:
                    target_nodes_data.append({
                        "node_id": node_id,
                        "data": node_data,
                        "fetch_success": True
                    })
                else:
                    target_nodes_data.append({
                        "node_id": node_id,
                        "data": None,
                        "fetch_success": False,
                        "error": "Node not found or fetch failed"
                    })

            except Exception as e:
                print(f"[DEBUG] [TARGET_NODES] Error fetching node {node_id}: {str(e)}")
                target_nodes_data.append({
                    "node_id": node_id,
                    "data": None,
                    "fetch_success": False,
                    "error": str(e)
                })

        return target_nodes_data

    async def _get_node_data(self, file_key: str, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get data for a specific node

        Args:
            file_key: Figma file key
            node_id: Node ID to fetch

        Returns:
            Node data or None if not found
        """
        try:
            # For now, we'll search in the existing pages data
            # In a full implementation, this would make a specific API call to get node details
            pages_result = await self.api_client.fetch_file_pages(file_key)

            if not pages_result.get("success", False):
                return None

            # Search for the node in pages data
            for page in pages_result.get("pages", []):
                for node in page.get("visible_nodes", []):
                    if node.get("id") == node_id:
                        return node

            return None

        except Exception as e:
            print(f"[DEBUG] [TARGET_NODES] Error getting node data for {node_id}: {str(e)}")
            return None

    async def fetch_pages_only(self, file_key: str) -> Dict[str, Any]:
        """
        Fetch pages without filtering or reporting

        Args:
            file_key: Figma file key

        Returns:
            Raw pages data
        """
        return await self.api_client.fetch_file_pages(file_key)

    def filter_only(self, pages_data: Dict[str, Any], **filter_kwargs) -> Dict[str, Any]:
        """
        Apply filtering without fetching or reporting

        Args:
            pages_data: Pages data to filter
            **filter_kwargs: Filter parameters

        Returns:
            Filtered result
        """
        filter_result = self.filter_engine.filter_nodes_by_criteria(pages_data, **filter_kwargs)

        # Convert FilterResult to dict for consistency
        return {
            "success": filter_result.success,
            "pages": filter_result.pages,
            "total_pages": filter_result.total_pages,
            "total_nodes": filter_result.total_nodes,
            "filter_criteria": filter_result.filter_criteria,
            "error": filter_result.error
        }

    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        try:
            config = self.config_manager.get_config()
            return {
                "naming_prefixes": {
                    "svg_exporter": config.naming_prefixes.svg_exporter,
                    "img_exporter": config.naming_prefixes.img_exporter,
                    "icon_exporter": config.naming_prefixes.icon_exporter
                },
                "filter_patterns": {
                    "include": config.filter_patterns.include,
                    "exclude": config.filter_patterns.exclude,
                    "case_sensitive": config.filter_patterns.case_sensitive
                },
                "api_settings": {
                    "base_url": config.api_settings.base_url,
                    "requests_per_minute": config.api_settings.requests_per_minute,
                    "timeout": config.api_settings.timeout
                },
                "output_settings": {
                    "default_output_dir": config.output_settings.default_output_dir,
                    "report_formats": config.output_settings.report_formats
                },
                "target_nodes": {
                    "enabled": config.target_nodes.enabled,
                    "node_ids": config.target_nodes.node_ids,
                    "export_mode": config.target_nodes.export_mode,
                    "process_children": config.target_nodes.process_children
                }
            }
        except Exception as e:
            return {"error": f"Failed to load config: {str(e)}"}

async def main():
    """Main function for standalone execution"""
    print("[DEBUG] FIGMA CLIENT MODULE v1.0 - MODULAR ARCHITECTURE")
    print("=" * 80)
    print("Figma API client with modular architecture")
    print()

    # Load credentials from environment
    try:
        import os
        import dotenv
        dotenv.load_dotenv()

        api_token = os.getenv('FIGMA_API_TOKEN')
        file_key = os.getenv('FIGMA_FILE_KEY')

        if not api_token or not file_key:
            print("[DEBUG] [CONFIG] Missing FIGMA_API_TOKEN or FIGMA_FILE_KEY environment variables")
            return False

        print(f"[DEBUG] [CONFIG] Using file key: {file_key}")

        # Initialize orchestrator with config
        async with FigmaClientOrchestrator(api_token) as orchestrator:
            # Show config summary
            config_summary = orchestrator.get_config_summary()
            if "error" not in config_summary:
                print("[DEBUG] [CONFIG] Configuration loaded:")
                print(f"[DEBUG] [CONFIG]   Include patterns: {config_summary['filter_patterns']['include']}")
                print(f"[DEBUG] [CONFIG]   Exclude patterns: {config_summary['filter_patterns']['exclude']}")
                print(f"[DEBUG] [CONFIG]   Output directory: {config_summary['output_settings']['default_output_dir']}")
                print()

            # Process file with full pipeline
            result = await orchestrator.process_file(file_key)

            if result["success"]:
                print("\n" + "=" * 80)
                print("[DEBUG] FIGMA CLIENT SUMMARY")
                print("=" * 80)
                print("[DEBUG] Status: SUCCESS")
                print(f"[DEBUG] Pages: {result.get('total_pages', 0)}")
                print(f"[DEBUG] Nodes: {result.get('total_nodes', 0)}")

                # Show filter statistics if available
                if "filter_criteria" in result and "statistics" in result["filter_criteria"]:
                    stats = result["filter_criteria"]["statistics"]
                    print(f"[DEBUG] Filtered from {stats.get('total_input_nodes', 0)} to {stats.get('total_filtered_nodes', 0)} nodes")

                return True
            else:
                print(f"[DEBUG] [ERROR] Processing failed: {result.get('error')}")
                return False

    except Exception as e:
        print(f"\n[DEBUG] [FATAL] Figma client failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n[DEBUG] Figma client {'completed successfully' if success else 'failed'}")

    sys.exit(0 if success else 1)