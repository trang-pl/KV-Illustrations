#!/usr/bin/env python3
"""
Diagnostic Test Script for Node ID 431-22256 from Figma URL
Tests both fetch data and processing logic to identify issues
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dotenv

# Load environment variables FIRST
dotenv.load_dotenv()

from server.services.figma_sync import FigmaSyncService, FigmaAPIClient
from config.settings import settings, reload_settings

# Reload settings after loading environment variables
reload_settings()


class DiagnosticConfig:
    """Diagnostic configuration for testing node 431-22256"""

    def __init__(self):
        # Target node ID from Figma URL
        self.target_node_id = "431-22256"

        # Alternative node IDs to try if main one fails
        self.fallback_node_ids = ["431:22256", "0:1"]  # Root node as fallback

        # Export config
        self.export_config = {
            "force_sync": True,
            "batch_size": 5,  # Smaller batch for diagnostic
            "delay_between_batches": 1.0,
            "max_retries": 3,
            "retry_delay": 2.0
        }

        # Output directories
        self.output_base = "./test/exports/node_431_22256_diagnostic"
        self.fetch_test_output = f"{self.output_base}/fetch_test"
        self.processing_test_output = f"{self.output_base}/processing_test"
        self.full_test_output = f"{self.output_base}/full_test"


class DataFetchValidator:
    """Validates data fetching capabilities"""

    def __init__(self, client: FigmaAPIClient):
        self.client = client
        self.results = {}

    async def test_node_accessibility(self, file_key: str, node_ids: list) -> Dict[str, Any]:
        """Test if nodes can be accessed"""
        print("\n[TEST] TESTING NODE ACCESSIBILITY...")

        accessibility_results = {}

        for node_id in node_ids:
            print(f"   Testing node: {node_id}")
            try:
                node_data = await self.client.get_node_structure(file_key, node_id)
                if node_data:
                    accessibility_results[node_id] = {
                        "accessible": True,
                        "name": node_data.get("name", "Unknown"),
                        "type": node_data.get("type", "Unknown"),
                        "children_count": len(node_data.get("children", [])),
                        "error": None
                    }
                    print(f"   [OK] {node_id}: {node_data.get('name')} ({node_data.get('type')})")
                else:
                    accessibility_results[node_id] = {
                        "accessible": False,
                        "name": None,
                        "type": None,
                        "children_count": 0,
                        "error": "No data returned"
                    }
                    print(f"   [ERROR] {node_id}: No data returned")

            except Exception as e:
                accessibility_results[node_id] = {
                    "accessible": False,
                    "name": None,
                    "type": None,
                    "children_count": 0,
                    "error": str(e)
                }
                print(f"   [ERROR] {node_id}: Error - {str(e)}")

        self.results["node_accessibility"] = accessibility_results
        return accessibility_results

    async def test_file_structure(self, file_key: str) -> Dict[str, Any]:
        """Test file structure retrieval"""
        print("\n[DIR] TESTING FILE STRUCTURE...")

        try:
            # Get root node
            root_node = await self.client.get_node_structure(file_key, "0:1")
            if not root_node:
                return {"error": "Cannot access root node"}

            # Analyze structure
            structure_info = {
                "root_name": root_node.get("name", "Unknown"),
                "root_type": root_node.get("type", "Unknown"),
                "total_children": len(root_node.get("children", [])),
                "exportable_nodes": 0,
                "component_count": 0,
                "frame_count": 0
            }

            def analyze_node(node):
                node_type = node.get("type", "")
                if node_type in ["COMPONENT", "INSTANCE", "FRAME"]:
                    structure_info["exportable_nodes"] += 1
                    if node_type == "COMPONENT":
                        structure_info["component_count"] += 1
                    elif node_type == "FRAME":
                        structure_info["frame_count"] += 1

                for child in node.get("children", []):
                    analyze_node(child)

            analyze_node(root_node)

            print("   [ANALYSIS] Structure Analysis:")
            print(f"      Root: {structure_info['root_name']} ({structure_info['root_type']})")
            print(f"      Total children: {structure_info['total_children']}")
            print(f"      Exportable nodes: {structure_info['exportable_nodes']}")
            print(f"      Components: {structure_info['component_count']}")
            print(f"      Frames: {structure_info['frame_count']}")

            self.results["file_structure"] = structure_info
            return structure_info

        except Exception as e:
            error_result = {"error": str(e)}
            self.results["file_structure"] = error_result
            print(f"   [ERROR] Structure test failed: {str(e)}")
            return error_result


class ProcessingLogicValidator:
    """Validates processing logic"""

    def __init__(self, service: FigmaSyncService):
        self.service = service
        self.results = {}

    async def test_export_processing(self, file_key: str, node_id: str, output_dir: str) -> Dict[str, Any]:
        """Test the export processing logic"""
        print(f"\n[PROCESS] TESTING EXPORT PROCESSING for node {node_id}...")

        try:
            # Test with minimal config first
            result = await self.service.process_sync(
                file_key=file_key,
                node_id=node_id,
                output_dir=output_dir,
                force_sync=True
            )

            processing_info = {
                "success": "error" not in result,
                "exported": result.get("exported", 0),
                "failed": result.get("failed", 0),
                "skipped": result.get("skipped", 0),
                "dev_ready": result.get("dev_ready", 0),
                "needs_review": result.get("needs_review", 0),
                "elapsed_time": result.get("elapsed_time", "N/A"),
                "error": result.get("error"),
                "details": result
            }

            print("   [STATS] Processing Results:")
            print(f"      Exported: {processing_info['exported']}")
            print(f"      Failed: {processing_info['failed']}")
            print(f"      Skipped: {processing_info['skipped']}")
            print(f"      Time: {processing_info['elapsed_time']}")

            if processing_info['error']:
                print(f"      Error: {processing_info['error']}")

            self.results["export_processing"] = processing_info
            return processing_info

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "exported": 0,
                "failed": 0,
                "skipped": 0
            }
            self.results["export_processing"] = error_result
            print(f"   [ERROR] Processing test failed: {str(e)}")
            return error_result


async def run_diagnostic_test():
    """Run complete diagnostic test for node 431-22256"""
    print("=" * 80)
    print("[DIAG] DIAGNOSTIC TEST FOR NODE 431-22256")
    print("=" * 80)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize config
    config = DiagnosticConfig()

    # Create output directories
    Path(config.fetch_test_output).mkdir(parents=True, exist_ok=True)
    Path(config.processing_test_output).mkdir(parents=True, exist_ok=True)
    Path(config.full_test_output).mkdir(parents=True, exist_ok=True)

    # Get environment variables
    token = os.environ.get('FIGMA_API_TOKEN')
    file_key = os.environ.get('FIGMA_FILE_KEY')

    if not token or not file_key:
        print("[ERROR] Missing FIGMA_API_TOKEN or FIGMA_FILE_KEY in environment")
        return {"error": "Missing environment variables"}

    print(f"[INFO] Using file key: {file_key}")
    print(f"[TARGET] Target node: {config.target_node_id}")

    # Initialize services
    api_client = FigmaAPIClient(token)
    sync_service = FigmaSyncService()

    # Phase 1: Data Fetch Validation
    print("\n" + "="*60)
    print("PHASE 1: DATA FETCH VALIDATION")
    print("="*60)

    fetch_validator = DataFetchValidator(api_client)

    # Test node accessibility
    node_ids_to_test = [config.target_node_id] + config.fallback_node_ids
    accessibility_results = await fetch_validator.test_node_accessibility(file_key, node_ids_to_test)

    # Test file structure
    structure_results = await fetch_validator.test_file_structure(file_key)

    # Phase 2: Processing Logic Validation
    print("\n" + "="*60)
    print("PHASE 2: PROCESSING LOGIC VALIDATION")
    print("="*60)

    processing_validator = ProcessingLogicValidator(sync_service)

    # Find best accessible node for processing test
    best_node_id = None
    for node_id, result in accessibility_results.items():
        if result["accessible"]:
            best_node_id = node_id
            break

    if best_node_id:
        print(f"[TARGET] Using accessible node for processing test: {best_node_id}")
        processing_results = await processing_validator.test_export_processing(
            file_key, best_node_id, config.processing_test_output
        )
    else:
        print("[ERROR] No accessible nodes found for processing test")
        processing_results = {"error": "No accessible nodes"}

    # Phase 3: Diagnostic Summary
    print("\n" + "="*60)
    print("PHASE 3: DIAGNOSTIC SUMMARY")
    print("="*60)

    diagnostic_summary = {
        "test_timestamp": datetime.now().isoformat(),
        "target_node": config.target_node_id,
        "file_key": file_key,
        "fetch_validation": fetch_validator.results,
        "processing_validation": processing_validator.results,
        "recommendations": []
    }

    # Generate recommendations
    if not accessibility_results.get(config.target_node_id, {}).get("accessible", False):
        diagnostic_summary["recommendations"].append(
            f"Target node {config.target_node_id} is not accessible. Check if node exists or permissions."
        )

    if structure_results.get("error"):
        diagnostic_summary["recommendations"].append(
            "File structure retrieval failed. Check API token and file permissions."
        )

    if processing_results.get("error"):
        diagnostic_summary["recommendations"].append(
            "Export processing failed. Check processing logic and configuration."
        )
    elif processing_results.get("exported", 0) == 0:
        diagnostic_summary["recommendations"].append(
            "No files were exported. Check if target node contains exportable elements."
        )

    # Save diagnostic results
    summary_file = f"{config.output_base}/diagnostic_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(diagnostic_summary, f, indent=2, ensure_ascii=False)

    print("[INFO] DIAGNOSTIC RESULTS:")
    print(f"   • Target node accessible: {accessibility_results.get(config.target_node_id, {}).get('accessible', False)}")
    print(f"   • File structure OK: {'error' not in structure_results}")
    print(f"   • Processing successful: {'error' not in processing_results}")
    print(f"   • Files exported: {processing_results.get('exported', 0)}")

    if diagnostic_summary["recommendations"]:
        print("\n[TIP] RECOMMENDATIONS:")
        for i, rec in enumerate(diagnostic_summary["recommendations"], 1):
            print(f"   {i}. {rec}")

    print(f"\n[DIR] Results saved to: {config.output_base}")
    print(f"[FILE] Summary file: {summary_file}")

    return diagnostic_summary


def print_test_header():
    """Print test header with environment info"""
    print("[ENV] ENVIRONMENT INFO:")
    print(f"   - Python: {sys.version}")
    print(f"   - Working directory: {os.getcwd()}")
    print(f"   - FIGMA_API_TOKEN: {'SET' if os.environ.get('FIGMA_API_TOKEN') else 'MISSING'}")
    print(f"   - FIGMA_FILE_KEY: {'SET' if os.environ.get('FIGMA_FILE_KEY') else 'MISSING'}")


async def main():
    """Main diagnostic function"""
    print_test_header()

    try:
        results = await run_diagnostic_test()

        # Exit code based on results
        has_critical_error = (
            "error" in results.get("fetch_validation", {}).get("file_structure", {}) or
            not any(result.get("accessible", False)
                   for result in results.get("fetch_validation", {}).get("node_accessibility", {}).values())
        )

        print(f"\n{'[OK]' if not has_critical_error else '[ERROR]'} DIAGNOSTIC COMPLETE")
        return results

    except KeyboardInterrupt:
        print("\n[STOP] Diagnostic stopped by user")
        return {"error": "Stopped by user"}
    except Exception as e:
        print(f"\n[CRASH] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    results = asyncio.run(main())
    sys.exit(0 if "error" not in str(results) else 1)