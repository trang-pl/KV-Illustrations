#!/usr/bin/env python3
"""
Production Pipeline Orchestrator v1.1 - Refactored
===============================================

Script chính ngắn gọn điều phối tất cả modules với naming convention mới.

Features:
- Import và orchestrate các sub modules
- Pipeline execution với dependency management
- Error handling và recovery
- Configuration-driven execution

Author: DS Tools - Modular Pipeline
Version: 1.1.0
Date: 2025-08-29
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import all modules using importlib for dynamic loading
import importlib.util

def load_module_from_file(module_name, file_path):
    """Load module from file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load all modules dynamically
modules_dir = Path(__file__).parent.parent / "modules"
credentials_loader = load_module_from_file("credentials_loader", modules_dir / "01-credentials-loader-v1.0.py")
# UPDATED: Use new unified processor instead of old modular client
figma_unified_processor = load_module_from_file("figma_unified_processor", modules_dir / "02-figma-unified-processor.py")
node_processor = load_module_from_file("node_processor", modules_dir / "03-node-processor-v1.0.py")
export_engine = load_module_from_file("export_engine", modules_dir / "04-export-engine-v1.0.py")
config_manager = load_module_from_file("config_manager", modules_dir / "02-config-manager.py")
filter_engine = load_module_from_file("filter_engine", modules_dir / "02-filter-engine.py")
api_client = load_module_from_file("api_client", modules_dir / "02-api-client.py")
report_generator_module = load_module_from_file("report_generator", modules_dir / "02-report-generator.py")
backup_manager = load_module_from_file("backup_manager", modules_dir / "06-backup-manager-v1.0.py")

# Extract classes
CredentialsLoader = credentials_loader.CredentialsLoader
# UPDATED: Use new unified processor
FigmaUnifiedProcessor = figma_unified_processor.FigmaUnifiedProcessor
NodeProcessor = node_processor.NodeProcessor
ExportEngine = export_engine.ExportEngine
ConfigManager = config_manager.ConfigManager
FilterEngine = filter_engine.FilterEngine
ApiClient = api_client.FigmaApiClient
ReportGenerator = report_generator_module.ReportGenerator
BackupManager = backup_manager.BackupManager

class ExecutionMode(Enum):
    """Pipeline execution modes"""
    PIPELINE = "pipeline"  # Full pipeline execution
    DIRECT = "direct"      # Individual module execution

class PipelineOrchestrator:
    """Main pipeline orchestrator với naming convention mới"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "scripts/config/pipeline_config.json"
        self.config = {}
        self.execution_mode = ExecutionMode.PIPELINE
        self.pipeline_results = {}

        # Module mapping với naming convention mới
        # UPDATED: Use unified processor instead of old figma_client
        self.module_classes = {
            "credentials_loader": CredentialsLoader,
            "figma_unified_processor": FigmaUnifiedProcessor,  # NEW: Unified processor
            "node_processor": NodeProcessor,
            "export_engine": ExportEngine,
            "config_manager": ConfigManager,
            "filter_engine": FilterEngine,
            "api_client": ApiClient,
            "report_generator": ReportGenerator,
            "backup_manager": BackupManager
        }

    async def load_configuration(self) -> Dict[str, Any]:
        """Load pipeline configuration"""
        print("[CONFIG] Loading pipeline configuration...")

        config_file = Path(self.config_path)
        if not config_file.exists():
            # Try relative path
            config_file = Path(__file__).parent.parent / "config" / "pipeline_config.json"

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        print("[SUCCESS] Configuration loaded successfully")
        return self.config

    async def execute_pipeline(self, target_stages: List[str] = None) -> Dict[str, Any]:
        """Execute the full pipeline hoặc selected stages"""
        print("\n[PIPELINE] PRODUCTION PIPELINE EXECUTION v1.1")
        print("=" * 80)

        start_time = datetime.now(timezone.utc)

        # Load configuration
        await self.load_configuration()

        # Determine stages to execute
        if target_stages:
            self.execution_mode = ExecutionMode.DIRECT
            stages_to_execute = [name for name in target_stages if name in self.module_classes]
        else:
            self.execution_mode = ExecutionMode.PIPELINE
            # Get enabled stages from config
            modules_config = self.config.get("modules", {})
            stages_to_execute = [name for name, config in modules_config.items()
                               if config.get("enabled", False)]

        print(f"[TARGET] Execution mode: {self.execution_mode.value}")
        print(f"[LIST] Stages to execute: {', '.join(stages_to_execute)}")

        # Execute stages
        stage_results = {}
        context = {}

        for stage_name in stages_to_execute:
            print(f"\n[STAGE] Executing stage: {stage_name}")
            print("-" * 60)

            try:
                result = await self._execute_stage(stage_name, context)
                stage_results[stage_name] = result
                self.pipeline_results[stage_name] = result

                # Update context for next stages
                context.update(self._build_execution_context(stage_results))

                if result.get("success", False):
                    print(f"[SUCCESS] Stage {stage_name} completed successfully")
                else:
                    print(f"[ERROR] Stage {stage_name} failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                print(f"[ERROR] Stage {stage_name} encountered error: {e}")
                stage_results[stage_name] = {
                    "success": False,
                    "error": str(e),
                    "stage": stage_name
                }

        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - start_time).total_seconds()

        # Calculate pipeline summary
        successful_stages = sum(1 for result in stage_results.values() if result.get("success", False))
        total_stages = len(stage_results)
        pipeline_success = successful_stages == total_stages

        summary = {
            "success": pipeline_success,
            "execution_mode": self.execution_mode.value,
            "total_stages": total_stages,
            "successful_stages": successful_stages,
            "failed_stages": total_stages - successful_stages,
            "total_duration": total_duration,
            "stages_executed": list(stage_results.keys()),
            "stage_results": stage_results,
            "timestamp": end_time.isoformat()
        }

        # Print final summary
        print("\n" + "=" * 80)
        print("[TARGET] PIPELINE EXECUTION SUMMARY")
        print("=" * 80)

        if pipeline_success:
            print("[SUCCESS] Pipeline Status: SUCCESS")
        else:
            print("[ERROR] Pipeline Status: FAILED")

        print(f"[STATS] Stages: {successful_stages}/{total_stages} successful")
        print(f"[TIME] Duration: {total_duration:.2f} seconds")
        print(f"[TARGET] Mode: {self.execution_mode.value}")

        return summary

    async def _execute_stage(self, stage_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single pipeline stage"""
        module_class = self.module_classes[stage_name]

        try:
            # Create module instance based on stage type
            if stage_name == "credentials_loader":
                module = module_class()
                result = await module.load_and_validate_credentials()
            elif stage_name == "figma_unified_processor":
                # UPDATED: Use new unified processor with complete unified logic
                api_token = context.get("credentials", {}).get("api_token", "")
                file_key = context.get("credentials", {}).get("file_key", "")
                async with module_class(api_token) as processor:
                    result = await processor.process_file_unified(file_key)
                    # Unified processor already generates comprehensive reports
                    # No need for separate save_client_report call
            elif stage_name == "node_processor":
                pages_data = context.get("figma_data", {})
                target_nodes = context.get("target_nodes", [])
                module = module_class()
                result = await module.process_nodes(pages_data, target_nodes)
                if result.get("success", False):
                    await module.save_processor_report(result)
            elif stage_name == "export_engine":
                processed_data = context.get("processed_data", {})
                file_key = context.get("credentials", {}).get("file_key", "")
                api_token = context.get("credentials", {}).get("api_token", "")
                module = module_class(api_token)
                result = await module.export_nodes_batch(processed_data, file_key)
                if result.get("success", False):
                    await module.save_export_report(result)
            elif stage_name == "api_client":
                api_token = context.get("credentials", {}).get("api_token", "")
                module = module_class(api_token)
                result = {"success": True, "message": "API client initialized"}
            elif stage_name == "report_generator":
                module = module_class()
                # Create sample data for report generation
                sample_data = {
                    "success": True,
                    "total_pages": 0,
                    "total_nodes": 0,
                    "file_name": "sample",
                    "pages": [],
                    "filter_criteria": {}
                }
                json_path, md_path = module.generate_reports(sample_data)
                result = {
                    "success": True,
                    "json_report": json_path,
                    "markdown_report": md_path,
                    "message": "Reports generated successfully"
                }
            elif stage_name == "backup_manager":
                export_dir = context.get("export_directory", "exports/production_deployment_test/")
                module = module_class()
                result = await module.create_directory_backup(export_dir)
            else:
                # config_manager, filter_engine use default initialization
                module = module_class()
                result = {"success": True, "message": f"{stage_name} initialized"}

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stage": stage_name
            }

    def _build_execution_context(self, stage_results: Dict[str, Any]) -> Dict[str, Any]:
        """Build execution context từ completed stages"""
        context = {}

        # Extract credentials
        if "credentials_loader" in stage_results:
            credentials_result = stage_results["credentials_loader"]
            if credentials_result.get("success"):
                context["credentials"] = credentials_result.get("credentials", {})

        # Extract Figma data
        # UPDATED: Use unified processor data
        if "figma_unified_processor" in stage_results:
            unified_result = stage_results["figma_unified_processor"]
            if unified_result.get("success"):
                context["figma_data"] = unified_result
                context["unified_processing_result"] = unified_result

        # Extract processed data
        if "node_processor" in stage_results:
            node_result = stage_results["node_processor"]
            if node_result.get("success"):
                context["processed_data"] = node_result

        # Extract export directory
        if "export_engine" in stage_results:
            export_result = stage_results["export_engine"]
            if export_result.get("success"):
                export_summary = export_result.get("summary", {})
                context["export_directory"] = export_summary.get("output_directory", "exports/export_engine/")

        # Add target nodes from config
        figma_config = self.config.get("figma", {})
        context["target_nodes"] = [figma_config.get("target_node")]

        return context

async def main():
    """Main function for pipeline execution"""
    print("[PIPELINE] PRODUCTION PIPELINE ORCHESTRATOR v1.1")
    print("=" * 80)

    # Parse command line arguments
    args = sys.argv[1:]

    if len(args) == 0:
        # Default: Execute full pipeline
        print("[INFO] No arguments provided. Executing full pipeline...")
        orchestrator = PipelineOrchestrator()
        result = await orchestrator.execute_pipeline()
    elif len(args) == 1 and args[0] in ["credentials_loader", "figma_unified_processor", "node_processor", "export_engine", "config_manager", "filter_engine", "api_client", "report_generator", "backup_manager"]:
        # Direct mode: Execute single module
        module_name = args[0]
        print(f"[INFO] Executing module in direct mode: {module_name}")
        orchestrator = PipelineOrchestrator()
        result = await orchestrator.execute_pipeline([module_name])
    else:
        print("[ERROR] Invalid arguments")
        print("Usage:")
        print("  python 01-production-pipeline-v1.1.py                    # Execute full pipeline")
        print("  python 01-production-pipeline-v1.1.py <module_name>     # Execute single module")
        print("Available modules: credentials_loader, figma_unified_processor, node_processor, export_engine, config_manager, filter_engine, api_client, report_generator, backup_manager")
        return False

    # Print final result
    if result.get("success"):
        print("\n[SUCCESS] Pipeline execution completed successfully!")
    else:
        print("\n[ERROR] Pipeline execution failed!")
        if "error" in result:
            print(f"Error: {result['error']}")

    return result.get("success", False)

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n[FINISH] Pipeline orchestrator {'completed successfully' if success else 'failed'}")
    sys.exit(0 if success else 1)