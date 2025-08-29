#!/usr/bin/env python3
"""
Report Generator Module v1.0
============================

Generate comprehensive reports từ processing results.
Creates JSON và Markdown reports với detailed analysis.

Features:
- JSON report generation
- Markdown report generation
- Processing statistics
- Error reporting
- Unicode-safe operations
- Timestamp tracking

Author: Kilo Code Debug Agent
Version: 1.0.0
Date: 2025-08-29
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class ReportGenerator:
    """Report generator for processing results"""

    def __init__(self, config_manager=None):
        """
        Initialize report generator

        Args:
            config_manager: Config manager instance (optional)
        """
        self.config_manager = config_manager
        print(f"[DEBUG] [REPORT_GENERATOR] ReportGenerator initialized")

    def generate_reports(self, result: Dict[str, Any], output_dir: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate JSON và Markdown reports từ processing result

        Args:
            result: Processing result dictionary
            output_dir: Output directory for reports (optional, uses config if not provided)

        Returns:
            Tuple of (json_report_path, markdown_report_path)
        """
        try:
            # Use config output directory if not provided
            if output_dir is None and self.config_manager:
                output_settings = self.config_manager.get_output_settings()
                output_dir = output_settings.default_output_dir
            elif output_dir is None:
                output_dir = "exports/reports"

            print(f"[DEBUG] [REPORT_GENERATOR] Generating reports to: {output_dir}")

            # Ensure output directory exists
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Generate timestamp for filenames
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

            # Generate JSON report
            json_report_path = self._generate_json_report(result, output_path, timestamp)

            # Generate Markdown report
            markdown_report_path = self._generate_markdown_report(result, output_path, timestamp)

            print(f"[DEBUG] [REPORT_GENERATOR] Reports generated:")
            print(f"  JSON: {json_report_path}")
            print(f"  Markdown: {markdown_report_path}")

            return str(json_report_path), str(markdown_report_path)

        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            print(f"[DEBUG] [REPORT_GENERATOR] {error_msg}")
            import traceback
            traceback.print_exc()
            return "", ""

    def _generate_json_report(self, result: Dict[str, Any], output_path: Path, timestamp: str) -> Path:
        """Generate detailed JSON report"""
        try:
            # Build comprehensive report data
            report_data = {
                "metadata": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "generator": "Figma Client Module v1.0",
                    "version": "1.0.0"
                },
                "processing_result": result,
                "statistics": self._calculate_statistics(result),
                "configuration": self._get_config_summary(),
                "system_info": {
                    "python_version": sys.version,
                    "platform": sys.platform
                }
            }

            # Generate filename
            filename = f"figma_processing_report_{timestamp}.json"
            report_path = output_path / filename

            # Write JSON report
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"[DEBUG] [REPORT_GENERATOR] JSON report saved: {report_path}")
            return report_path

        except Exception as e:
            print(f"[DEBUG] [REPORT_GENERATOR] Error generating JSON report: {str(e)}")
            # Return empty path on error
            return output_path / f"error_report_{timestamp}.json"

    def _generate_markdown_report(self, result: Dict[str, Any], output_path: Path, timestamp: str) -> Path:
        """Generate human-readable Markdown report"""
        try:
            # Build Markdown content
            markdown_content = self._build_markdown_content(result, timestamp)

            # Generate filename
            filename = f"figma_processing_report_{timestamp}.md"
            report_path = output_path / filename

            # Write Markdown report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"[DEBUG] [REPORT_GENERATOR] Markdown report saved: {report_path}")
            return report_path

        except Exception as e:
            print(f"[DEBUG] [REPORT_GENERATOR] Error generating Markdown report: {str(e)}")
            # Return empty path on error
            return output_path / f"error_report_{timestamp}.md"

    def _calculate_statistics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate processing statistics"""
        try:
            stats = {
                "success": result.get("success", False),
                "total_pages": result.get("total_pages", 0),
                "total_nodes": result.get("total_nodes", 0),
                "processing_time": None,
                "average_nodes_per_page": 0,
                "filter_applied": False,
                "filter_statistics": {}
            }

            # Calculate average nodes per page
            if stats["total_pages"] > 0:
                stats["average_nodes_per_page"] = stats["total_nodes"] / stats["total_pages"]

            # Check for filter criteria
            filter_criteria = result.get("filter_criteria", {})
            if filter_criteria:
                stats["filter_applied"] = True
                stats["filter_statistics"] = {
                    "include": filter_criteria.get("include", []),
                    "exclude": filter_criteria.get("exclude", []),
                    "case_sensitive": filter_criteria.get("case_sensitive", False)
                }

            # Add page-level statistics
            pages = result.get("pages", [])
            page_stats = []
            for page in pages:
                page_stats.append({
                    "name": page.get("name", "Unknown"),
                    "node_count": page.get("node_count", 0),
                    "id": page.get("id", "")
                })

            stats["page_details"] = page_stats

            return stats

        except Exception as e:
            print(f"[DEBUG] [REPORT_GENERATOR] Error calculating statistics: {str(e)}")
            return {"error": str(e)}

    def _get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        try:
            if not self.config_manager:
                return {"status": "No config manager available"}

            config_summary = self.config_manager.get_config_summary()
            return config_summary

        except Exception as e:
            print(f"[DEBUG] [REPORT_GENERATOR] Error getting config summary: {str(e)}")
            return {"error": str(e)}

    def _build_markdown_content(self, result: Dict[str, Any], timestamp: str) -> str:
        """Build Markdown report content"""
        try:
            lines = []

            # Header
            lines.append("# Figma Processing Report")
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

            # Statistics
            lines.append("## Processing Statistics")
            lines.append("")
            lines.append(f"- **Total Pages:** {result.get('total_pages', 0)}")
            lines.append(f"- **Total Nodes:** {result.get('total_nodes', 0)}")

            # Filter information
            filter_criteria = result.get("filter_criteria", {})
            if filter_criteria:
                lines.append("")
                lines.append("### Filter Criteria")
                lines.append("")
                include_patterns = filter_criteria.get("include", [])
                exclude_patterns = filter_criteria.get("exclude", [])
                case_sensitive = filter_criteria.get("case_sensitive", False)

                if include_patterns:
                    lines.append(f"- **Include Patterns:** {', '.join(include_patterns)}")
                if exclude_patterns:
                    lines.append(f"- **Exclude Patterns:** {', '.join(exclude_patterns)}")
                lines.append(f"- **Case Sensitive:** {'Yes' if case_sensitive else 'No'}")

            # Page Details
            pages = result.get("pages", [])
            if pages:
                lines.append("")
                lines.append("## Page Details")
                lines.append("")

                for page in pages:
                    page_name = page.get("name", "Unknown")
                    node_count = page.get("node_count", 0)
                    page_id = page.get("id", "")

                    lines.append(f"### {page_name}")
                    lines.append(f"- **Node Count:** {node_count}")
                    lines.append(f"- **Page ID:** {page_id}")

                    # Show sample nodes
                    visible_nodes = page.get("visible_nodes", [])
                    if visible_nodes:
                        lines.append("- **Sample Nodes:**")
                        for i, node in enumerate(visible_nodes[:5]):  # Show first 5 nodes
                            node_name = node.get("name", "Unknown")
                            node_type = node.get("type", "Unknown")
                            lines.append(f"  - {node_name} ({node_type})")

                        if len(visible_nodes) > 5:
                            lines.append(f"  - ... and {len(visible_nodes) - 5} more nodes")

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
                        lines.append(f"- Icon Exporter: `{naming.get('icon_exporter', 'N/A')}`")
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
            lines.append("*Generated by Figma Client Module v1.0*")
            lines.append("*Report Generator v1.0.0*")

            return "\n".join(lines)

        except Exception as e:
            error_content = f"""# Figma Processing Report

**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

## Status: ❌ ERROR

**Error:** Report generation failed: {str(e)}

---
*Generated by Figma Client Module v1.0*
"""
            return error_content

# Export main class
__all__ = ['ReportGenerator']