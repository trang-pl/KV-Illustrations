#!/usr/bin/env python3
"""
Report Generator Module v1.0
============================

Generate comprehensive reports và metadata từ pipeline execution.

Features:
- Comprehensive deployment reports
- Performance metrics và analytics
- Export statistics và summaries
- Target node verification reports
- Executive summaries
- Trend analysis và insights

Author: DS Tools - Modular Pipeline
Version: 1.0.0
Date: 2025-08-29
"""

import json
import sys
import statistics
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

# Fix Windows encoding issues (disabled to avoid conflicts)
# if sys.platform == "win32":
#     import codecs
#     sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
#     sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class PipelineMetrics:
    """Represents comprehensive pipeline metrics"""
    total_execution_time: float
    module_execution_times: Dict[str, float]
    success_rate: float
    error_count: int
    files_exported: int
    nodes_processed: int
    target_nodes_found: int
    average_naming_score: float

class ReportGenerator:
    """Generate comprehensive reports từ pipeline execution data"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "scripts/config/pipeline_config.json"
        # Adjust path if running from modules directory
        if not Path(self.config_path).exists():
            self.config_path = "../config/pipeline_config.json"
        self.reports = {}
        self.metrics = {}

    async def load_config(self) -> Dict[str, Any]:
        """Load pipeline configuration"""
        print("[CONFIG] Loading pipeline configuration...")

        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        print("[SUCCESS] Configuration loaded successfully")
        return config

    def aggregate_pipeline_data(self, pipeline_results: Dict[str, Any]) -> PipelineMetrics:
        """Aggregate data từ tất cả pipeline modules"""
        print("[AGGREGATE] Aggregating pipeline data...")

        # Extract data từ từng module
        credentials_data = pipeline_results.get("credentials", {})
        figma_data = pipeline_results.get("figma_client", {})
        processor_data = pipeline_results.get("node_processor", {})
        export_data = pipeline_results.get("export_engine", {})

        # Calculate execution times
        module_times = {}
        total_time = 0

        if credentials_data and credentials_data.get("processing_time"):
            module_times["credentials_loader"] = credentials_data["processing_time"]
            total_time += credentials_data["processing_time"]

        if figma_data and figma_data.get("response_time"):
            module_times["figma_client"] = figma_data["response_time"]
            total_time += figma_data["response_time"]

        if processor_data and processor_data.get("summary", {}).get("processing_time"):
            module_times["node_processor"] = processor_data["summary"]["processing_time"]
            total_time += processor_data["summary"]["processing_time"]

        if export_data and export_data.get("summary", {}).get("total_time"):
            module_times["export_engine"] = export_data["summary"]["total_time"]
            total_time += export_data["summary"]["total_time"]

        # Calculate success metrics
        export_summary = export_data.get("summary", {})
        total_jobs = export_summary.get("total_jobs", 0)
        completed_jobs = export_summary.get("completed_jobs", 0)
        success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0

        # Calculate other metrics
        nodes_processed = processor_data.get("summary", {}).get("total_nodes", 0)
        target_nodes_found = processor_data.get("summary", {}).get("target_nodes_found", 0)
        avg_naming_score = processor_data.get("summary", {}).get("average_naming_score", 0)

        # Count errors
        error_count = 0
        if credentials_data.get("error"):
            error_count += 1
        if figma_data.get("error"):
            error_count += 1
        if processor_data.get("error"):
            error_count += 1
        if export_data.get("error"):
            error_count += 1

        metrics = PipelineMetrics(
            total_execution_time=total_time,
            module_execution_times=module_times,
            success_rate=success_rate,
            error_count=error_count,
            files_exported=completed_jobs,
            nodes_processed=nodes_processed,
            target_nodes_found=target_nodes_found,
            average_naming_score=avg_naming_score
        )

        print("[SUCCESS] Pipeline data aggregated successfully")
        return metrics

    def generate_deployment_report(self, pipeline_results: Dict[str, Any],
                                 metrics: PipelineMetrics) -> str:
        """Generate comprehensive deployment report"""
        print("[REPORT] Generating deployment report...")

        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

        report = f"""# Production Pipeline Deployment Report

**Timestamp:** {timestamp}
**Pipeline Version:** 1.0.0

## Executive Summary

"""

        # Overall status
        overall_success = all([
            pipeline_results.get("credentials", {}).get("success", False),
            pipeline_results.get("figma_client", {}).get("success", False),
            pipeline_results.get("node_processor", {}).get("success", False),
            pipeline_results.get("export_engine", {}).get("success", False)
        ])

        if overall_success:
            report += "✅ **DEPLOYMENT STATUS: SUCCESS**\n\n"
            report += "The production pipeline completed successfully with all modules functioning correctly.\n\n"
        else:
            report += "❌ **DEPLOYMENT STATUS: FAILED**\n\n"
            report += "The production pipeline encountered errors. See detailed analysis below.\n\n"

        # Key metrics
        report += f"""## Key Performance Metrics

| Metric | Value |
|--------|-------|
| Total Execution Time | {metrics.total_execution_time:.2f} seconds |
| Success Rate | {metrics.success_rate:.1f}% |
| Files Exported | {metrics.files_exported} |
| Nodes Processed | {metrics.nodes_processed} |
| Target Nodes Found | {metrics.target_nodes_found} |
| Average Naming Score | {metrics.average_naming_score:.1f}% |
| Error Count | {metrics.error_count} |

## Module Performance

"""

        # Module breakdown
        for module_name, exec_time in metrics.module_execution_times.items():
            status = "✅ Success" if pipeline_results.get(module_name.replace("_", "_"), {}).get("success", False) else "❌ Failed"
            report += f"### {module_name.replace('_', ' ').title()}\n\n"
            report += f"- **Status:** {status}\n"
            report += f"- **Execution Time:** {exec_time:.2f} seconds\n"
            report += f"- **Time Share:** {(exec_time/metrics.total_execution_time*100):.1f}%\n\n"

        # Detailed analysis
        report += "## Detailed Analysis\n\n"

        # Credentials analysis
        credentials = pipeline_results.get("credentials", {})
        if credentials:
            report += "### Credentials Validation\n\n"
            if credentials.get("success"):
                report += "✅ Credentials validated successfully\n\n"
                masked_token = credentials.get("masked_token", "N/A")
                report += f"- **API Token:** {masked_token}\n"
                report += f"- **Connectivity:** {'✅ Connected' if credentials.get('connectivity', {}).get('success') else '❌ Failed'}\n"
            else:
                report += f"❌ Credentials validation failed: {credentials.get('error', 'Unknown error')}\n"
            report += "\n"

        # Figma client analysis
        figma_client = pipeline_results.get("figma_client", {})
        if figma_client:
            report += "### Figma API Operations\n\n"
            if figma_client.get("success"):
                report += "✅ Figma API operations completed successfully\n\n"
                report += f"- **Pages Processed:** {figma_client.get('total_pages', 0)}\n"
                report += f"- **Nodes Discovered:** {figma_client.get('total_nodes', 0)}\n"
                report += f"- **File Name:** {figma_client.get('file_name', 'N/A')}\n"
            else:
                report += f"❌ Figma API operations failed: {figma_client.get('error', 'Unknown error')}\n"
            report += "\n"

        # Node processor analysis
        node_processor = pipeline_results.get("node_processor", {})
        if node_processor:
            report += "### Node Processing\n\n"
            if node_processor.get("success"):
                summary = node_processor.get("summary", {})
                report += "✅ Node processing completed successfully\n\n"
                report += f"- **Total Nodes:** {summary.get('total_nodes', 0)}\n"
                report += f"- **Export Ready:** {summary.get('export_ready_nodes', 0)}\n"
                report += f"- **Validation Errors:** {summary.get('validation_errors', 0)}\n"
                report += f"- **Naming Accuracy:** {summary.get('average_naming_score', 0):.1f}%\n"
            else:
                report += f"❌ Node processing failed: {node_processor.get('error', 'Unknown error')}\n"
            report += "\n"

        # Export engine analysis
        export_engine = pipeline_results.get("export_engine", {})
        if export_engine:
            report += "### Export Operations\n\n"
            if export_engine.get("success"):
                summary = export_engine.get("summary", {})
                report += "✅ Export operations completed successfully\n\n"
                report += f"- **Jobs Processed:** {summary.get('total_jobs', 0)}\n"
                report += f"- **Successful Exports:** {summary.get('completed_jobs', 0)}\n"
                report += f"- **Failed Exports:** {summary.get('failed_jobs', 0)}\n"
                report += f"- **Batches Processed:** {summary.get('batches_processed', 0)}\n"
                report += f"- **Output Directory:** `{summary.get('output_directory', 'N/A')}`\n"

                # Validation results
                validation = export_engine.get("validation", {})
                if validation:
                    report += f"- **Valid Files:** {validation.get('valid_files', 0)}/{validation.get('total_files', 0)}\n"
            else:
                report += f"❌ Export operations failed: {export_engine.get('error', 'Unknown error')}\n"
            report += "\n"

        # Recommendations
        report += "## Recommendations\n\n"

        if metrics.error_count > 0:
            report += "### Issues to Address\n\n"
            if metrics.success_rate < 90:
                report += "- **Low Success Rate:** Investigate export failures and improve error handling\n"
            if metrics.average_naming_score < 70:
                report += "- **Poor Naming Convention:** Review and improve node naming standards\n"
            if metrics.target_nodes_found == 0:
                report += "- **Missing Target Nodes:** Verify target node IDs and file structure\n"
            report += "\n"

        if overall_success:
            report += "### Optimization Opportunities\n\n"
            if metrics.total_execution_time > 300:  # 5 minutes
                report += "- **Performance:** Consider optimizing API calls and batch processing\n"
            if metrics.success_rate < 100:
                report += "- **Reliability:** Implement retry mechanisms for failed operations\n"
            report += "\n"

        # Next steps
        report += "## Next Steps\n\n"
        if overall_success:
            report += "1. **Monitor Production:** Set up monitoring for exported assets\n"
            report += "2. **Validate Assets:** Verify exported files meet design requirements\n"
            report += "3. **Schedule Regular Exports:** Set up automated pipeline execution\n"
            report += "4. **Performance Tuning:** Optimize based on this execution's metrics\n"
        else:
            report += "1. **Investigate Failures:** Review error logs and fix identified issues\n"
            report += "2. **Test Fixes:** Run pipeline again with corrections\n"
            report += "3. **Improve Error Handling:** Add better error recovery mechanisms\n"
            report += "4. **Update Documentation:** Document lessons learned from this execution\n"

        return report

    def generate_executive_summary(self, pipeline_results: Dict[str, Any],
                                 metrics: PipelineMetrics) -> str:
        """Generate executive summary cho stakeholders"""
        print("[SUMMARY] Generating executive summary...")

        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

        summary = f"""# Executive Summary - Production Pipeline Execution

**Report Date:** {timestamp}
**Pipeline Version:** 1.0.0

## Deployment Overview

"""

        # Status overview
        overall_success = all([
            pipeline_results.get("credentials", {}).get("success", False),
            pipeline_results.get("figma_client", {}).get("success", False),
            pipeline_results.get("node_processor", {}).get("success", False),
            pipeline_results.get("export_engine", {}).get("success", False)
        ])

        if overall_success:
            summary += "🟢 **STATUS: SUCCESSFUL DEPLOYMENT**\n\n"
            summary += "The production pipeline executed successfully, delivering all expected assets.\n\n"
        else:
            summary += "🔴 **STATUS: DEPLOYMENT ISSUES**\n\n"
            summary += "The production pipeline encountered issues requiring attention.\n\n"

        # Key achievements
        summary += "## Key Achievements\n\n"

        if metrics.files_exported > 0:
            summary += f"✅ **{metrics.files_exported} assets** successfully exported\n"
        if metrics.target_nodes_found > 0:
            summary += f"✅ **{metrics.target_nodes_found} target nodes** identified and processed\n"
        if metrics.success_rate >= 90:
            summary += f"✅ **{metrics.success_rate:.1f}% success rate** achieved\n"
        if metrics.average_naming_score >= 80:
            summary += f"✅ **High naming quality** ({metrics.average_naming_score:.1f}% average score)\n"

        summary += "\n"

        # Performance highlights
        summary += "## Performance Highlights\n\n"
        summary += f"- **Execution Time:** {metrics.total_execution_time:.1f} seconds\n"
        summary += f"- **Nodes Processed:** {metrics.nodes_processed}\n"
        summary += f"- **System Efficiency:** {metrics.success_rate:.1f}% success rate\n"
        summary += f"- **Quality Score:** {metrics.average_naming_score:.1f}% naming accuracy\n\n"

        # Risk assessment
        summary += "## Risk Assessment\n\n"

        risk_level = "LOW"
        risk_factors = []

        if metrics.error_count > 0:
            risk_factors.append(f"{metrics.error_count} errors encountered")
            risk_level = "MEDIUM"

        if metrics.success_rate < 95:
            risk_factors.append(f"Success rate below 95% ({metrics.success_rate:.1f}%)")
            risk_level = "MEDIUM"

        if metrics.target_nodes_found == 0:
            risk_factors.append("No target nodes found")
            risk_level = "HIGH"

        if not risk_factors:
            summary += "🟢 **Risk Level: LOW**\n\n"
            summary += "No significant issues detected. Pipeline is operating within normal parameters.\n\n"
        else:
            if risk_level == "MEDIUM":
                summary += "🟡 **Risk Level: MEDIUM**\n\n"
            else:
                summary += "🔴 **Risk Level: HIGH**\n\n"

            summary += "Issues requiring attention:\n\n"
            for factor in risk_factors:
                summary += f"- {factor}\n"
            summary += "\n"

        # Business impact
        summary += "## Business Impact\n\n"

        if overall_success and metrics.success_rate >= 95:
            summary += "✅ **POSITIVE IMPACT**\n\n"
            summary += "- Assets delivered on time and within quality standards\n"
            summary += "- Pipeline demonstrates reliability for production use\n"
            summary += "- Foundation established for automated asset management\n\n"
        elif overall_success:
            summary += "⚠️ **MODERATE IMPACT**\n\n"
            summary += "- Assets delivered but with some quality concerns\n"
            summary += "- Process improvements needed before full automation\n"
            summary += "- Manual verification recommended for this execution\n\n"
        else:
            summary += "❌ **NEGATIVE IMPACT**\n\n"
            summary += "- Asset delivery incomplete or compromised\n"
            summary += "- Immediate attention required to resolve pipeline issues\n"
            summary += "- Alternative asset sourcing may be necessary\n\n"

        # Recommendations
        summary += "## Strategic Recommendations\n\n"

        if overall_success:
            summary += "1. **Scale Operations:** Pipeline ready for increased production load\n"
            summary += "2. **Automate Scheduling:** Implement regular automated executions\n"
            summary += "3. **Monitor Performance:** Establish ongoing performance tracking\n"
            summary += "4. **Team Training:** Train team on pipeline operation and monitoring\n"
        else:
            summary += "1. **Immediate Resolution:** Address critical pipeline failures\n"
            summary += "2. **Root Cause Analysis:** Investigate underlying causes of issues\n"
            summary += "3. **Process Improvement:** Implement fixes and quality controls\n"
            summary += "4. **Backup Procedures:** Ensure alternative asset delivery methods\n"

        return summary

    async def generate_comprehensive_reports(self, pipeline_results: Dict[str, Any],
                                           output_dir: str = "exports/report_generator/"):
        """Generate tất cả comprehensive reports"""
        print("[REPORTS] Generating comprehensive report suite...")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Aggregate metrics
        metrics = self.aggregate_pipeline_data(pipeline_results)

        # Generate reports
        deployment_report = self.generate_deployment_report(pipeline_results, metrics)
        executive_summary = self.generate_executive_summary(pipeline_results, metrics)

        # Save deployment report
        deployment_file = output_path / "production_deployment_final_report.md"
        with open(deployment_file, 'w', encoding='utf-8') as f:
            f.write(deployment_report)

        # Save executive summary
        summary_file = output_path / "executive_summary_report.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(executive_summary)

        # Save metrics data
        metrics_file = output_path / "pipeline_metrics.json"
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metrics": {
                    "total_execution_time": metrics.total_execution_time,
                    "module_execution_times": metrics.module_execution_times,
                    "success_rate": metrics.success_rate,
                    "error_count": metrics.error_count,
                    "files_exported": metrics.files_exported,
                    "nodes_processed": metrics.nodes_processed,
                    "target_nodes_found": metrics.target_nodes_found,
                    "average_naming_score": metrics.average_naming_score
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pipeline_version": "1.0.0"
            }, f, indent=2, ensure_ascii=False)

        print("[SUCCESS] Comprehensive reports generated successfully")
        print(f"[REPORTS] Reports saved to: {output_path}")

        return {
            "success": True,
            "reports": {
                "deployment_report": str(deployment_file),
                "executive_summary": str(summary_file),
                "metrics_data": str(metrics_file)
            },
            "metrics": {
                "total_execution_time": metrics.total_execution_time,
                "success_rate": metrics.success_rate,
                "files_exported": metrics.files_exported,
                "error_count": metrics.error_count
            }
        }

    async def save_report_summary(self, result: Dict[str, Any],
                                output_dir: str = "exports/report_generator/"):
        """Save report generation summary"""
        print("[SUMMARY] Saving report generation summary...")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save summary
        summary_file = output_path / "report_generation_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# Report Generation Summary\n\n")
            f.write(f"**Timestamp:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")

            if result.get("success"):
                f.write("## ✅ Report Generation Successful\n\n")
                reports = result.get("reports", {})
                f.write(f"- **Deployment Report:** `{reports.get('deployment_report', 'N/A')}`\n")
                f.write(f"- **Executive Summary:** `{reports.get('executive_summary', 'N/A')}`\n")
                f.write(f"- **Metrics Data:** `{reports.get('metrics_data', 'N/A')}`\n\n")

                metrics = result.get("metrics", {})
                f.write("## 📊 Key Metrics\n\n")
                f.write(f"- **Total Execution Time:** {metrics.get('total_execution_time', 0):.2f} seconds\n")
                f.write(f"- **Success Rate:** {metrics.get('success_rate', 0):.1f}%\n")
                f.write(f"- **Files Exported:** {metrics.get('files_exported', 0)}\n")
                f.write(f"- **Error Count:** {metrics.get('error_count', 0)}\n")
            else:
                f.write("## ❌ Report Generation Failed\n\n")
                f.write(f"**Error:** {result.get('error', 'Unknown error')}\n\n")

        print(f"[SUCCESS] Summary saved to: {output_path}")
        return str(summary_file)

async def main():
    """Main function for standalone execution"""
    print("REPORT GENERATOR MODULE v1.0")
    print("=" * 80)
    print("Generate comprehensive reports và metadata")
    print()

    # For standalone execution, create sample data
    print("[INFO] This module is designed to work within the pipeline")
    print("[INFO] Use the pipeline orchestrator for full functionality")
    print()

    # Create sample pipeline results for testing
    sample_results = {
        "credentials": {"success": True, "processing_time": 1.2},
        "figma_client": {"success": True, "response_time": 5.8, "total_pages": 3, "total_nodes": 45},
        "node_processor": {
            "success": True,
            "summary": {
                "total_nodes": 45,
                "export_ready_nodes": 32,
                "target_nodes_found": 2,
                "validation_errors": 3,
                "average_naming_score": 85.5,
                "processing_time": 2.1
            }
        },
        "export_engine": {
            "success": True,
            "summary": {
                "total_jobs": 32,
                "completed_jobs": 30,
                "failed_jobs": 2,
                "batches_processed": 4,
                "total_time": 45.2,
                "output_directory": "exports/export_engine/"
            }
        }
    }

    generator = ReportGenerator()
    result = await generator.generate_comprehensive_reports(sample_results)
    await generator.save_report_summary(result)

    print("\n" + "=" * 80)
    print("REPORT GENERATOR SUMMARY")
    print("=" * 80)
    print("Status: Module loaded successfully")
    print("Use pipeline orchestrator for full processing")

    return True

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    print(f"\nReport generator {'completed successfully' if success else 'failed'}")

    sys.exit(0 if success else 1)
