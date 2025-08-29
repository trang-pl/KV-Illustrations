#!/usr/bin/env python3
"""
Pipeline Data Flow Debug Script
==============================

Debug script to test data flow between pipeline stages and identify data integrity issues.

Author: Kilo Code Debug Agent
Date: 2025-08-29
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import modules
import importlib.util

def load_module_from_file(module_name, file_path):
    """Load module from file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

async def test_figma_client_data_flow():
    """Test figma client data flow"""
    print("[DEBUG] Testing Figma Client Data Flow")
    print("=" * 60)

    try:
        # Load credentials
        credentials_loader_module = load_module_from_file("credentials_loader", "scripts/modules/01-credentials-loader-v1.0.py")
        CredentialsLoader = credentials_loader_module.CredentialsLoader
        credentials_loader = CredentialsLoader()
        creds_result = await credentials_loader.load_and_validate_credentials()

        if not creds_result.get("success"):
            print("[ERROR] Failed to load credentials")
            return None

        api_token = creds_result["credentials"]["api_token"]
        file_key = creds_result["credentials"]["file_key"]

        print(f"[SUCCESS] Credentials loaded: {file_key}")

        # Load figma client
        figma_client_module = load_module_from_file("figma_client", "scripts/modules/02-figma-client-fixed-v1.0.py")
        FigmaClient = figma_client_module.FigmaClient

        async with FigmaClient(api_token) as client:
            # Test fetch_file_pages
            print("[PAGE] Testing fetch_file_pages...")
            pages_result = await client.fetch_file_pages(file_key)

            print(f"[RESULT] Result success: {pages_result.get('success', False)}")
            print(f"[RESULT] Total pages: {pages_result.get('total_pages', 0)}")
            print(f"[RESULT] Total nodes: {pages_result.get('total_nodes', 0)}")

            if pages_result.get("success"):
                pages = pages_result.get("pages", [])
                print(f"[RESULT] Pages list length: {len(pages)}")

                if pages:
                    first_page = pages[0]
                    print(f"[RESULT] First page type: {type(first_page)}")
                    print(f"[RESULT] First page name: {getattr(first_page, 'name', 'N/A')}")
                    print(f"[RESULT] First page node count: {getattr(first_page, 'node_count', 0)}")

                    visible_nodes = getattr(first_page, 'visible_nodes', [])
                    print(f"[RESULT] First page visible nodes: {len(visible_nodes)}")

                    if visible_nodes:
                        first_node = visible_nodes[0]
                        print(f"[RESULT] First node type: {type(first_node)}")
                        print(f"[RESULT] First node name: {getattr(first_node, 'name', 'N/A')}")
                        print(f"[RESULT] First node id: {getattr(first_node, 'id', 'N/A')}")

            return pages_result

    except Exception as e:
        print(f"[ERROR] Figma client test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_node_processor_data_flow(figma_data):
    """Test node processor data flow"""
    print("\n[DEBUG] Testing Node Processor Data Flow")
    print("=" * 60)

    try:
        # Load node processor
        node_processor_module = load_module_from_file("node_processor", "scripts/modules/03-node-processor-v1.0.py")
        NodeProcessor = node_processor_module.NodeProcessor

        processor = NodeProcessor()

        # Test with figma data
        print("[PROCESS] Testing process_nodes...")
        target_nodes = ["431:22256"]  # From config
        result = await processor.process_nodes(figma_data, target_nodes)

        print(f"[RESULT] Result success: {result.get('success', False)}")
        print(f"[RESULT] Processed nodes: {len(result.get('processed_nodes', []))}")
        print(f"[RESULT] Export ready: {result.get('summary', {}).get('export_ready_nodes', 0)}")
        print(f"[RESULT] Target nodes found: {len(result.get('target_nodes', []))}")

        return result

    except Exception as e:
        print(f"[ERROR] Node processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_export_engine_data_flow(processed_data):
    """Test export engine data flow"""
    print("\n[DEBUG] Testing Export Engine Data Flow")
    print("=" * 60)

    try:
        # Load credentials for API token
        credentials_loader_module = load_module_from_file("credentials_loader", "scripts/modules/01-credentials-loader-v1.0.py")
        CredentialsLoader = credentials_loader_module.CredentialsLoader
        credentials_loader = CredentialsLoader()
        creds_result = await credentials_loader.load_and_validate_credentials()

        if not creds_result.get("success"):
            print("[ERROR] Failed to load credentials for export engine")
            return None

        api_token = creds_result["credentials"]["api_token"]
        file_key = creds_result["credentials"]["file_key"]

        # Load export engine
        export_engine_module = load_module_from_file("export_engine", "scripts/modules/04-export-engine-v1.0.py")
        ExportEngine = export_engine_module.ExportEngine

        async with ExportEngine(api_token) as engine:
            # Test create_export_jobs
            print("[JOBS] Testing create_export_jobs...")
            processed_nodes = processed_data.get("processed_nodes", [])
            print(f"[RESULT] Input processed nodes: {len(processed_nodes)}")

            export_jobs = engine.create_export_jobs(processed_nodes)
            print(f"[RESULT] Export jobs created: {len(export_jobs)}")

            if export_jobs:
                first_job = export_jobs[0]
                print(f"[RESULT] First job node_id: {first_job.node_id}")
                print(f"[RESULT] First job node_name: {first_job.node_name}")

            # Test export_nodes_batch with minimal data
            print("[EXPORT] Testing export_nodes_batch...")
            try:
                result = await engine.export_nodes_batch(processed_data, file_key)
                print(f"[RESULT] Export result success: {result.get('success', False)}")
                print(f"[RESULT] Exported files: {len(result.get('exported_files', {}))}")
                return result
            except Exception as export_error:
                print(f"[ERROR] Export failed with error: {export_error}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": str(export_error)}

    except Exception as e:
        print(f"[ERROR] Export engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main debug function"""
    print("[DEBUG] PIPELINE DATA FLOW DEBUG v1.0")
    print("=" * 80)

    # Test 1: Figma Client
    figma_data = await test_figma_client_data_flow()
    if not figma_data or not figma_data.get("success"):
        print("[ERROR] Figma client test failed - cannot continue")
        return False

    # Test 2: Node Processor
    processed_data = await test_node_processor_data_flow(figma_data)
    if not processed_data or not processed_data.get("success"):
        print("[ERROR] Node processor test failed - cannot continue")
        return False

    # Test 3: Export Engine
    export_result = await test_export_engine_data_flow(processed_data)
    if not export_result or not export_result.get("success"):
        print("[ERROR] Export engine test failed")
        return False

    print("\n[SUCCESS] All data flow tests passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n[FINISH] Data flow debug {'completed successfully' if success else 'failed'}")
    sys.exit(0 if success else 1)