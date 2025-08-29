#!/usr/bin/env python3
"""
Test Node Processor with Real Data from Figma Client
==================================================

Load data from Figma client reports and run node processor.

Author: DS Tools - Integration Test
Date: 2025-08-29
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import functions from node processor module
sys.path.insert(0, str(project_root / "scripts" / "modules"))

async def load_figma_client_data():
    """Load data from Figma client report"""
    print("[DATA] Loading Figma client data...")

    # Load from exports/figma_client/
    data_file = Path("exports/figma_client/figma_client_report.json")

    if not data_file.exists():
        print(f"[ERROR] Figma client data file not found: {data_file}")
        return None

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"[SUCCESS] Loaded data with {data.get('total_nodes', 0)} nodes from {data.get('total_pages', 0)} pages")
    return data

def create_node_objects(pages_data):
    """Create node objects from pages data"""
    print("[CONVERT] Creating node objects...")

    # Simple node class
    class SimpleNode:
        def __init__(self, node_data, page_name):
            self.id = node_data['id']
            self.name = node_data['name']
            self.type = node_data['type']
            self.page_id = node_data['page_id']
            self.page_name = page_name

    # Simple page class
    class SimplePage:
        def __init__(self, page_data):
            self.id = page_data['id']
            self.name = page_data['name']
            self.visible_nodes = [
                SimpleNode(node, page_data['name'])
                for node in page_data.get('visible_nodes', [])
            ]

    # Convert pages
    converted_pages = []
    for page_data in pages_data.get('pages', []):
        converted_pages.append(SimplePage(page_data))

    # Return in format expected by processor
    result = pages_data.copy()
    result['pages'] = converted_pages

    print(f"[SUCCESS] Created {len(converted_pages)} pages with {sum(len(p.visible_nodes) for p in converted_pages)} nodes")
    return result

async def run_node_processor_with_real_data():
    """Run node processor with real data"""
    print("NODE PROCESSOR INTEGRATION TEST")
    print("=" * 80)
    print("Testing with real data from Figma client")
    print()

    try:
        # Step 1: Load Figma client data
        print("[STEP 1] Loading Figma client data...")
        raw_data = await load_figma_client_data()
        if not raw_data:
            print("[ERROR] No data available for processing")
            return False

        # Step 2: Convert to node objects
        print("\n[STEP 2] Converting to node objects...")
        pages_data = create_node_objects(raw_data)

        # Step 3: Import và khởi tạo Node Processor
        print("\n[STEP 3] Initializing Node Processor...")

        # Import the module directly
        spec = None
        for path in sys.path:
            module_path = Path(path) / "03-node-processor-v1.0.py"
            if module_path.exists():
                spec = module_path
                break

        if not spec:
            print("[ERROR] Could not find node processor module")
            return False

        # Execute the module to get the classes
        exec(open(spec).read())

        # Get the NodeProcessor class from globals
        if 'NodeProcessor' not in globals():
            print("[ERROR] NodeProcessor class not found in module")
            return False

        processor = globals()['NodeProcessor']()

        # Step 4: Load config
        print("\n[STEP 4] Loading configuration...")
        config = await processor.load_config()
        print(f"[CONFIG] Loaded: {config['pipeline']['name']} v{config['pipeline']['version']}")

        # Step 5: Process nodes
        print("\n[STEP 5] Processing nodes...")
        target_node_ids = ["431:22256"]  # svg_exporter_thumbnail-rasterized
        result = await processor.process_nodes(pages_data, target_node_ids)

        # Step 6: Filter export-ready nodes
        print("\n[STEP 6] Filtering export-ready nodes...")
        filtered_result = await processor.filter_export_ready_nodes(result)

        # Step 7: Save reports
        print("\n[STEP 7] Saving reports...")
        report_file, summary_file = await processor.save_processor_report(
            filtered_result,
            output_dir="exports/node_processor/"
        )

        # Step 8: Display results
        print("\n" + "=" * 80)
        print("PROCESSING RESULTS")
        print("=" * 80)

        if result.get("success"):
            summary = result.get("summary", {})
            print("[SUCCESS] Processing Successful")
            print(f"   Total Nodes: {summary.get('total_nodes', 0)}")
            print(f"   Target Nodes Found: {summary.get('target_nodes_found', 0)}")
            print(f"   Export Ready: {summary.get('export_ready_nodes', 0)}")
            print(f"   Validation Errors: {summary.get('validation_errors', 0)}")
            print(f"   Average Naming Score: {summary.get('average_naming_score', 0):.1f}%")
            print(f"   Processing Time: {summary.get('processing_time', 0):.2f}s")

            # Show target nodes
            target_nodes = result.get("target_nodes", [])
            if target_nodes:
                print(f"   Target Nodes: {', '.join(target_nodes)}")

            # Show sample processed nodes
            processed_nodes = result.get("processed_nodes", [])
            if processed_nodes:
                print("\nSample Processed Nodes:")
                for i, node in enumerate(processed_nodes[:3]):
                    status = "[READY]" if node.get("export_ready") else "[PENDING]"
                    target = "[TARGET]" if node.get("is_target") else ""
                    print(f"      {status}{target} {node.get('name')} (Score: {node.get('naming_score')}%)")

            print(f"\nReports saved to: {report_file}")
            print(f"Summary: {summary_file}")

        else:
            print("[FAILED] Processing Failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")

        return result.get("success", False)

    except Exception as e:
        print(f"[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    start_time = datetime.now(timezone.utc)
    print(f"[START] Test started at: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    success = await run_node_processor_with_real_data()

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Status: {'PASSED' if success else 'FAILED'}")
    print(f"Duration: {duration:.2f}s")
    print(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\nTest {'completed successfully' if success else 'failed'}")

    sys.exit(0 if success else 1)