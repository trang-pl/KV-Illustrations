#!/usr/bin/env python3
"""
Figma Unified Processor Module v1.0
===================================

Unified architecture for Figma file processing with complete data fetch,
unified filtering logic (prefix + target nodes), and comprehensive reporting.

NEW LOGIC FLOW:
1. Fetch complete Figma file (all pages)
2. From complete data -> Filter simultaneously by:
   - Prefix naming (svg_exporter_*, img_exporter_*)
   - Target node IDs (if enabled)
3. Generate unified reports

Features:
- Complete data fetch (all pages)
- Unified filtering algorithm (prefix + target nodes)
- Comprehensive reporting (1 set reports with all data)
- Config management (figma_client_config.json)
- Robust error handling and recovery
- Performance monitoring
- Unicode-safe operations

Author: Kilo Code Debug Agent
Version: 1.0.0
Date: 2025-08-29
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Set
from datetime import datetime, timezone
from dataclasses import dataclass

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

@dataclass
class UnifiedFilterCriteria:
    """Unified filter criteria combining prefix và target nodes"""
    prefix_patterns: List[str]
    target_node_ids: List[str]
    case_sensitive: bool
    process_children: bool

@dataclass
class UnifiedProcessingResult:
    """Result of unified processing operation"""
    success: bool
    file_key: str
    total_pages: int
    total_nodes: int
    filtered_pages: int
    filtered_nodes: int
    target_nodes_found: int
    prefix_matches: int
    processing_time: float
    filter_criteria: UnifiedFilterCriteria
    pages_data: List[Dict[str, Any]]
    target_nodes_data: List[Dict[str, Any]]
    error: Optional[str] = None

class FigmaUnifiedProcessor:
    """Unified processor for complete Figma file processing"""

    def __init__(self, api_token: str, config_path: Optional[str] = None):
        """
        Initialize unified processor

        Args:
            api_token: Figma API token
            config_path: Path to configuration file
        """
        self.api_token = api_token
        self.config_path = config_path

        # Initialize components
        self.config_manager = ConfigManager(config_path)
        self.api_client = FigmaApiClient(api_token, self.config_manager)

        # Processing state
        self.processing_start_time = None

        print(f"[DEBUG] [UNIFIED_PROCESSOR] FigmaUnifiedProcessor initialized")
        print(f"[DEBUG] [UNIFIED_PROCESSOR] Config path: {self.config_manager.config_path}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.api_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.api_client.__aexit__(exc_type, exc_val, exc_tb)

    async def process_file_unified(self, file_key: str) -> UnifiedProcessingResult:
        """
        Process Figma file với unified architecture

        NEW LOGIC FLOW:
        1. Fetch toàn bộ Figma file (tất cả pages)
        2. Filter đồng thời theo prefix + target nodes
        3. Generate unified reports

        Args:
            file_key: Figma file key

        Returns:
            UnifiedProcessingResult với complete processing data
        """
        self.processing_start_time = time.time()

        try:
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Starting unified processing for file: {file_key}")
            print(f"[DEBUG] [UNIFIED_PROCESSOR] NEW LOGIC FLOW:")
            print(f"  1. Fetch complete Figma file (all pages)")
            print(f"  2. Filter simultaneously by prefix + target nodes")
            print(f"  3. Generate unified reports")

            # Step 1: Fetch complete file data (all pages)
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Step 1: Fetching complete file data...")
            complete_data = await self._fetch_complete_file_data(file_key)

            if not complete_data["success"]:
                return self._create_error_result(file_key, complete_data.get("error", "Failed to fetch file data"))

            # Step 2: Create unified filter criteria
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Step 2: Creating unified filter criteria...")
            filter_criteria = self._create_unified_filter_criteria()

            # Step 3: Apply unified filtering (prefix + target nodes)
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Step 3: Applying unified filtering...")
            filtered_result = await self._apply_unified_filtering(complete_data, filter_criteria)

            # Step 4: Generate comprehensive reports
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Step 4: Generating comprehensive reports...")
            await self._generate_unified_reports(filtered_result)

            processing_time = time.time() - self.processing_start_time

            # Create final result
            result = UnifiedProcessingResult(
                success=True,
                file_key=file_key,
                total_pages=complete_data.get("total_pages", 0),
                total_nodes=complete_data.get("total_nodes", 0),
                filtered_pages=len(filtered_result.get("pages", [])),
                filtered_nodes=sum(page.get("node_count", 0) for page in filtered_result.get("pages", [])),
                target_nodes_found=len(filtered_result.get("target_nodes_data", [])),
                prefix_matches=filtered_result.get("prefix_matches", 0),
                processing_time=processing_time,
                filter_criteria=filter_criteria,
                pages_data=filtered_result.get("pages", []),
                target_nodes_data=filtered_result.get("target_nodes_data", [])
            )

            print(f"[DEBUG] [UNIFIED_PROCESSOR] Unified processing completed successfully")
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Processing time: {processing_time:.2f}s")
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Results: {result.filtered_pages} pages, {result.filtered_nodes} nodes")

            return result

        except Exception as e:
            processing_time = time.time() - self.processing_start_time if self.processing_start_time else 0
            error_msg = f"Unified processing failed: {str(e)}"
            print(f"[DEBUG] [UNIFIED_PROCESSOR] {error_msg}")
            import traceback
            traceback.print_exc()
            return self._create_error_result(file_key, error_msg, processing_time)

    async def _fetch_complete_file_data(self, file_key: str) -> Dict[str, Any]:
        """
        Fetch complete file data (all pages)

        Args:
            file_key: Figma file key

        Returns:
            Complete file data dictionary
        """
        try:
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Fetching complete file data for: {file_key}")

            # Fetch all pages data
            pages_result = await self.api_client.fetch_file_pages(file_key)

            if not pages_result.get("success", False):
                return {
                    "success": False,
                    "error": pages_result.get("error", "Failed to fetch pages"),
                    "file_key": file_key
                }

            # Calculate total statistics
            total_pages = len(pages_result.get("pages", []))
            total_nodes = sum(len(page.get("visible_nodes", [])) for page in pages_result.get("pages", []))

            print(f"[DEBUG] [UNIFIED_PROCESSOR] Fetched {total_pages} pages with {total_nodes} total nodes")

            return {
                "success": True,
                "file_key": file_key,
                "pages": pages_result.get("pages", []),
                "total_pages": total_pages,
                "total_nodes": total_nodes,
                "fetch_timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            error_msg = f"Complete data fetch failed: {str(e)}"
            print(f"[DEBUG] [UNIFIED_PROCESSOR] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "file_key": file_key
            }

    def _create_unified_filter_criteria(self) -> UnifiedFilterCriteria:
        """
        Create unified filter criteria từ config

        Returns:
            UnifiedFilterCriteria object
        """
        try:
            # Get prefix patterns từ config
            filter_patterns = self.config_manager.get_filter_patterns()
            prefix_patterns = filter_patterns.include if filter_patterns else ["svg_exporter_*", "img_exporter_*"]

            # Get target nodes config
            target_nodes = self.config_manager.get_target_nodes()
            target_node_ids = target_nodes.node_ids if target_nodes and target_nodes.enabled else []
            process_children = target_nodes.process_children if target_nodes else True

            # Get case sensitivity
            case_sensitive = filter_patterns.case_sensitive if filter_patterns else False

            criteria = UnifiedFilterCriteria(
                prefix_patterns=prefix_patterns,
                target_node_ids=target_node_ids,
                case_sensitive=case_sensitive,
                process_children=process_children
            )

            print(f"[DEBUG] [UNIFIED_PROCESSOR] Unified filter criteria:")
            print(f"  Prefix patterns: {criteria.prefix_patterns}")
            print(f"  Target node IDs: {criteria.target_node_ids}")
            print(f"  Case sensitive: {criteria.case_sensitive}")
            print(f"  Process children: {criteria.process_children}")

            return criteria

        except Exception as e:
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Error creating filter criteria: {str(e)}")
            # Return default criteria
            return UnifiedFilterCriteria(
                prefix_patterns=["svg_exporter_*", "img_exporter_*"],
                target_node_ids=[],
                case_sensitive=False,
                process_children=True
            )

    async def _apply_unified_filtering(self, complete_data: Dict[str, Any],
                                     filter_criteria: UnifiedFilterCriteria) -> Dict[str, Any]:
        """
        Apply unified filtering (prefix + target nodes simultaneously)

        Args:
            complete_data: Complete file data
            filter_criteria: Unified filter criteria

        Returns:
            Filtered result dictionary
        """
        try:
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Applying unified filtering...")

            filtered_pages = []
            target_nodes_data = []
            prefix_matches = 0

            # Track target node IDs for matching
            target_node_ids_set = set(filter_criteria.target_node_ids) if filter_criteria.target_node_ids else set()

            for page in complete_data.get("pages", []):
                page_id = page.get("id")
                page_name = page.get("name", "Unnamed Page")
                visible_nodes = page.get("visible_nodes", [])

                filtered_nodes = []
                page_target_nodes = []

                for node in visible_nodes:
                    node_id = node.get("id")
                    node_name = node.get("name", "")
                    node_type = node.get("type", "")

                    # Check unified filtering criteria
                    matches_prefix = self._matches_prefix_pattern(node_name, filter_criteria.prefix_patterns, filter_criteria.case_sensitive)
                    matches_target = node_id in target_node_ids_set if target_node_ids_set else False

                    # Include node if it matches EITHER prefix OR target node
                    should_include = matches_prefix or matches_target

                    if should_include:
                        filtered_nodes.append(node)

                        if matches_prefix:
                            prefix_matches += 1
                            print(f"[DEBUG] [UNIFIED_PROCESSOR] PREFIX MATCH: '{node_name}' (type: {node_type})")

                        if matches_target:
                            page_target_nodes.append({
                                "node_id": node_id,
                                "node_name": node_name,
                                "node_type": node_type,
                                "page_id": page_id,
                                "page_name": page_name,
                                "match_type": "target_node"
                            })
                            print(f"[DEBUG] [UNIFIED_PROCESSOR] TARGET MATCH: '{node_name}' (ID: {node_id})")

                # Include page if it has any filtered nodes
                if filtered_nodes:
                    filtered_page = {
                        "id": page_id,
                        "name": page_name,
                        "node_count": len(filtered_nodes),
                        "visible_nodes": filtered_nodes,
                        "target_nodes_in_page": len(page_target_nodes)
                    }
                    filtered_pages.append(filtered_page)

                    # Add target nodes from this page
                    target_nodes_data.extend(page_target_nodes)

                    print(f"[DEBUG] [UNIFIED_PROCESSOR] Page '{page_name}': {len(filtered_nodes)} nodes ({len(page_target_nodes)} target nodes)")

            result = {
                "success": True,
                "pages": filtered_pages,
                "target_nodes_data": target_nodes_data,
                "prefix_matches": prefix_matches,
                "filter_criteria": {
                    "prefix_patterns": filter_criteria.prefix_patterns,
                    "target_node_ids": filter_criteria.target_node_ids,
                    "case_sensitive": filter_criteria.case_sensitive,
                    "process_children": filter_criteria.process_children
                }
            }

            print(f"[DEBUG] [UNIFIED_PROCESSOR] Unified filtering completed:")
            print(f"  Filtered pages: {len(filtered_pages)}")
            print(f"  Total filtered nodes: {sum(len(page.get('visible_nodes', [])) for page in filtered_pages)}")
            print(f"  Target nodes found: {len(target_nodes_data)}")
            print(f"  Prefix matches: {prefix_matches}")

            return result

        except Exception as e:
            error_msg = f"Unified filtering failed: {str(e)}"
            print(f"[DEBUG] [UNIFIED_PROCESSOR] {error_msg}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": error_msg,
                "pages": [],
                "target_nodes_data": [],
                "prefix_matches": 0
            }

    def _matches_prefix_pattern(self, node_name: str, patterns: List[str], case_sensitive: bool) -> bool:
        """
        Check if node name matches any prefix pattern

        Args:
            node_name: Name of the node
            patterns: List of wildcard patterns
            case_sensitive: Case sensitivity flag

        Returns:
            True if matches any pattern
        """
        if not patterns:
            return False

        import re
        import fnmatch

        for pattern in patterns:
            if case_sensitive:
                if fnmatch.fnmatch(node_name, pattern):
                    return True
            else:
                if fnmatch.fnmatch(node_name.lower(), pattern.lower()):
                    return True

        return False

    async def _generate_unified_reports(self, filtered_result: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generate comprehensive unified reports

        Args:
            filtered_result: Filtered processing result

        Returns:
            Tuple of (json_report_path, markdown_report_path)
        """
        try:
            # Get output directory từ config
            output_settings = self.config_manager.get_output_settings()
            output_dir = output_settings.default_output_dir

            print(f"[DEBUG] [UNIFIED_PROCESSOR] Generating unified reports to: {output_dir}")

            # Ensure output directory exists
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Generate timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

            # Generate comprehensive JSON report
            json_report_path = self._generate_unified_json_report(filtered_result, output_path, timestamp)

            # Generate comprehensive Markdown report
            markdown_report_path = self._generate_unified_markdown_report(filtered_result, output_path, timestamp)

            print(f"[DEBUG] [UNIFIED_PROCESSOR] Unified reports generated:")
            print(f"  JSON: {json_report_path}")
            print(f"  Markdown: {markdown_report_path}")

            return str(json_report_path), str(markdown_report_path)

        except Exception as e:
            error_msg = f"Unified report generation failed: {str(e)}"
            print(f"[DEBUG] [UNIFIED_PROCESSOR] {error_msg}")
            import traceback
            traceback.print_exc()
            return "", ""

    def _generate_unified_json_report(self, result: Dict[str, Any], output_path: Path, timestamp: str) -> Path:
        """Generate comprehensive unified JSON report"""
        try:
            # Build comprehensive report data
            report_data = {
                "metadata": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "generator": "Figma Unified Processor v1.0",
                    "version": "1.0.0",
                    "architecture": "Unified (Complete Fetch + Unified Filtering + Comprehensive Reports)"
                },
                "processing_result": result,
                "unified_statistics": self._calculate_unified_statistics(result),
                "configuration": self._get_unified_config_summary(),
                "logic_flow": {
                    "step_1": "Fetch complete Figma file (all pages)",
                    "step_2": "Filter simultaneously by prefix + target nodes",
                    "step_3": "Generate unified reports"
                },
                "system_info": {
                    "python_version": sys.version,
                    "platform": sys.platform
                }
            }

            # Generate filename
            filename = f"figma_unified_processing_report_{timestamp}.json"
            report_path = output_path / filename

            # Write JSON report
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"[DEBUG] [UNIFIED_PROCESSOR] Unified JSON report saved: {report_path}")
            return report_path

        except Exception as e:
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Error generating unified JSON report: {str(e)}")
            return output_path / f"unified_error_report_{timestamp}.json"

    def _generate_unified_markdown_report(self, result: Dict[str, Any], output_path: Path, timestamp: str) -> Path:
        """Generate comprehensive unified Markdown report"""
        try:
            # Build Markdown content
            markdown_content = self._build_unified_markdown_content(result, timestamp)

            # Generate filename
            filename = f"figma_unified_processing_report_{timestamp}.md"
            report_path = output_path / filename

            # Write Markdown report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"[DEBUG] [UNIFIED_PROCESSOR] Unified Markdown report saved: {report_path}")
            return report_path

        except Exception as e:
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Error generating unified Markdown report: {str(e)}")
            return output_path / f"unified_error_report_{timestamp}.md"

    def _calculate_unified_statistics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive unified statistics"""
        try:
            stats = {
                "success": result.get("success", False),
                "filtered_pages": len(result.get("pages", [])),
                "filtered_nodes": sum(page.get("node_count", 0) for page in result.get("pages", [])),
                "target_nodes_found": len(result.get("target_nodes_data", [])),
                "prefix_matches": result.get("prefix_matches", 0),
                "filter_criteria": result.get("filter_criteria", {}),
                "unified_efficiency": 0,
                "target_node_coverage": 0
            }

            # Calculate unified efficiency
            total_filtered = stats["filtered_nodes"]
            if total_filtered > 0:
                target_contribution = stats["target_nodes_found"]
                prefix_contribution = stats["prefix_matches"]
                stats["unified_efficiency"] = (target_contribution + prefix_contribution) / total_filtered

            # Calculate target node coverage
            expected_targets = len(stats["filter_criteria"].get("target_node_ids", []))
            if expected_targets > 0:
                stats["target_node_coverage"] = stats["target_nodes_found"] / expected_targets

            return stats

        except Exception as e:
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Error calculating unified statistics: {str(e)}")
            return {"error": str(e)}

    def _get_unified_config_summary(self) -> Dict[str, Any]:
        """Get unified configuration summary"""
        try:
            if not self.config_manager:
                return {"status": "No config manager available"}

            config_summary = self.config_manager.get_config_summary()
            return config_summary

        except Exception as e:
            print(f"[DEBUG] [UNIFIED_PROCESSOR] Error getting unified config summary: {str(e)}")
            return {"error": str(e)}

    def _build_unified_markdown_content(self, result: Dict[str, Any], timestamp: str) -> str:
        """Build comprehensive unified Markdown report content"""
        try:
            lines = []

            # Header
            lines.append("# Figma Unified Processing Report")
            lines.append("")
            lines.append("## Architecture: Unified Processing")
            lines.append("")
            lines.append("**NEW LOGIC FLOW:**")
            lines.append("1. Fetch complete Figma file (all pages)")
            lines.append("2. Filter simultaneously by prefix + target nodes")
            lines.append("3. Generate unified reports")
            lines.append("")
            lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
            lines.append(f"**Timestamp:** {timestamp}")
            lines.append("")

            # Status
            success = result.get("success", False)
            status_emoji = "✅" if success else "❌"
            lines.append(f"## Status: {status_emoji} {'SUCCESS' if success else 'FAILED'}")
            lines.append("")

            if not success:
                error = result.get("error", "Unknown error")
                lines.append(f"**Error:** {error}")
                lines.append("")
                return "\n".join(lines)

            # Unified Statistics
            lines.append("## Unified Processing Statistics")
            lines.append("")
            pages = result.get("pages", [])
            target_nodes = result.get("target_nodes_data", [])
            prefix_matches = result.get("prefix_matches", 0)

            lines.append(f"- **Filtered Pages:** {len(pages)}")
            lines.append(f"- **Filtered Nodes:** {sum(page.get('node_count', 0) for page in pages)}")
            lines.append(f"- **Target Nodes Found:** {len(target_nodes)}")
            lines.append(f"- **Prefix Matches:** {prefix_matches}")
            lines.append("")

            # Filter Criteria
            filter_criteria = result.get("filter_criteria", {})
            if filter_criteria:
                lines.append("### Unified Filter Criteria")
                lines.append("")
                prefix_patterns = filter_criteria.get("prefix_patterns", [])
                target_node_ids = filter_criteria.get("target_node_ids", [])
                case_sensitive = filter_criteria.get("case_sensitive", False)

                if prefix_patterns:
                    lines.append(f"- **Prefix Patterns:** {', '.join(prefix_patterns)}")
                if target_node_ids:
                    lines.append(f"- **Target Node IDs:** {', '.join(target_node_ids)}")
                lines.append(f"- **Case Sensitive:** {'Yes' if case_sensitive else 'No'}")
                lines.append("")

            # Page Details
            if pages:
                lines.append("## Filtered Pages Details")
                lines.append("")

                for page in pages:
                    page_name = page.get("name", "Unknown")
                    node_count = page.get("node_count", 0)
                    target_nodes_in_page = page.get("target_nodes_in_page", 0)

                    lines.append(f"### {page_name}")
                    lines.append(f"- **Node Count:** {node_count}")
                    lines.append(f"- **Target Nodes in Page:** {target_nodes_in_page}")

                    # Show sample nodes
                    visible_nodes = page.get("visible_nodes", [])
                    if visible_nodes:
                        lines.append("- **Sample Nodes:**")
                        for i, node in enumerate(visible_nodes[:3]):  # Show first 3 nodes
                            node_name = node.get("name", "Unknown")
                            node_type = node.get("type", "Unknown")
                            node_id = node.get("id", "")
                            lines.append(f"  - {node_name} ({node_type}) - ID: {node_id}")

                        if len(visible_nodes) > 3:
                            lines.append(f"  - ... and {len(visible_nodes) - 3} more nodes")

                    lines.append("")

            # Target Nodes Details
            if target_nodes:
                lines.append("## Target Nodes Details")
                lines.append("")

                for target_node in target_nodes:
                    node_name = target_node.get("node_name", "Unknown")
                    node_id = target_node.get("node_id", "")
                    page_name = target_node.get("page_name", "Unknown")

                    lines.append(f"### {node_name}")
                    lines.append(f"- **Node ID:** {node_id}")
                    lines.append(f"- **Page:** {page_name}")
                    lines.append(f"- **Match Type:** {target_node.get('match_type', 'target_node')}")
                    lines.append("")

            # Configuration
            if self.config_manager:
                lines.append("## Configuration Summary")
                lines.append("")
                try:
                    config_summary = self.config_manager.get_config_summary()
                    if "error" not in config_summary:
                        # Naming prefixes
                        naming = config_summary.get("naming_prefixes", {})
                        lines.append("### Naming Prefixes")
                        lines.append(f"- SVG Exporter: `{naming.get('svg_exporter', 'N/A')}`")
                        lines.append(f"- IMG Exporter: `{naming.get('img_exporter', 'N/A')}`")
                        lines.append("")

                        # Output settings
                        output = config_summary.get("output_settings", {})
                        lines.append("### Output Settings")
                        lines.append(f"- Default Output Directory: `{output.get('default_output_dir', 'N/A')}`")
                        lines.append(f"- Report Formats: {', '.join(output.get('report_formats', []))}")
                        lines.append("")
                    else:
                        lines.append(f"**Config Error:** {config_summary.get('error')}")
                        lines.append("")
                except Exception as e:
                    lines.append(f"**Config Error:** {str(e)}")
                    lines.append("")

            # Footer
            lines.append("---")
            lines.append("")
            lines.append("*Generated by Figma Unified Processor v1.0*")
            lines.append("*Unified Architecture: Complete Fetch + Unified Filtering + Comprehensive Reports*")

            return "\n".join(lines)

        except Exception as e:
            error_content = f"""# Figma Unified Processing Report

**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

## Status: ❌ ERROR

**Error:** Unified report generation failed: {str(e)}

---
*Generated by Figma Unified Processor v1.0*
"""
            return error_content

    def _create_error_result(self, file_key: str, error_msg: str,
                           processing_time: float = 0) -> UnifiedProcessingResult:
        """Create error result"""
        return UnifiedProcessingResult(
            success=False,
            file_key=file_key,
            total_pages=0,
            total_nodes=0,
            filtered_pages=0,
            filtered_nodes=0,
            target_nodes_found=0,
            prefix_matches=0,
            processing_time=processing_time,
            filter_criteria=UnifiedFilterCriteria(
                prefix_patterns=[],
                target_node_ids=[],
                case_sensitive=False,
                process_children=True
            ),
            pages_data=[],
            target_nodes_data=[],
            error=error_msg
        )

async def main():
    """Main function for standalone execution"""
    print("[DEBUG] FIGMA UNIFIED PROCESSOR MODULE v1.0")
    print("=" * 80)
    print("Unified architecture: Complete Fetch + Unified Filtering + Comprehensive Reports")
    print()

    # Load credentials từ environment
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

        # Initialize unified processor
        async with FigmaUnifiedProcessor(api_token) as processor:
            # Process file với unified architecture
            result = await processor.process_file_unified(file_key)

            if result.success:
                print("\n" + "=" * 80)
                print("[DEBUG] FIGMA UNIFIED PROCESSOR SUMMARY")
                print("=" * 80)
                print("[DEBUG] Status: SUCCESS")
                print(f"[DEBUG] Architecture: Unified (Complete Fetch + Unified Filtering + Comprehensive Reports)")
                print(f"[DEBUG] Total Pages: {result.total_pages}")
                print(f"[DEBUG] Total Nodes: {result.total_nodes}")
                print(f"[DEBUG] Filtered Pages: {result.filtered_pages}")
                print(f"[DEBUG] Filtered Nodes: {result.filtered_nodes}")
                print(f"[DEBUG] Target Nodes Found: {result.target_nodes_found}")
                print(f"[DEBUG] Prefix Matches: {result.prefix_matches}")
                print(f"[DEBUG] Processing Time: {result.processing_time:.2f}s")

                return True
            else:
                print(f"[DEBUG] [ERROR] Unified processing failed: {result.error}")
                return False

    except Exception as e:
        print(f"\n[DEBUG] [FATAL] Figma unified processor failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n[DEBUG] Figma unified processor {'completed successfully' if success else 'failed'}")

    sys.exit(0 if success else 1)