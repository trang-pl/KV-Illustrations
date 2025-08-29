#!/usr/bin/env python3
"""
Script để chạy Module 03 với data từ Module 02
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import module 03
sys.path.insert(0, str(project_root / "scripts" / "modules"))

# Import the actual module file
import importlib.util
node_processor_spec = importlib.util.spec_from_file_location("node_processor", project_root / "scripts" / "modules" / "03-node-processor-v1.0.py")
node_processor = importlib.util.module_from_spec(node_processor_spec)
node_processor_spec.loader.exec_module(node_processor)
NodeProcessor = node_processor.NodeProcessor

async def main():
    """Chạy module 03 với data từ module 02"""

    print("Chay Module 03 (Node Processor) voi data tu Module 02")
    print("=" * 80)

    # Load data tu module 02 report (try latest figma_client report first)
    figma_client_dir = project_root / "exports" / "figma_client"

    # Find latest figma processing report
    latest_report = None
    if figma_client_dir.exists():
        json_files = list(figma_client_dir.glob("figma_processing_report_*.json"))
        if json_files:
            latest_report = max(json_files, key=lambda x: x.stat().st_mtime)

    if latest_report and latest_report.exists():
        report_path = latest_report
    else:
        # Fallback to old pipeline report
        pipeline_report = project_root / "exports" / "pipeline_execution" / "figma_processing_report_20250829_063209.json"
        if pipeline_report.exists():
            report_path = pipeline_report
        else:
            print(f"ERROR: Khong tim thay report tu module 02")
            print(f"  Tried latest figma_client report")
            print(f"  Tried: {pipeline_report}")
            return False

    if not report_path.exists():
        print(f"ERROR: Khong tim thay report tu module 02: {report_path}")
        return False

    print(f"Loading data tu: {report_path}")

    with open(report_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # Extract pages data from nested structure if needed
    if "processing_result" in raw_data:
        pages_data = raw_data["processing_result"]
    else:
        pages_data = raw_data

    print(f"SUCCESS: Data loaded: {pages_data.get('total_pages', 0)} pages, {pages_data.get('total_nodes', 0)} nodes")

    # Khoi tao Node Processor
    processor = NodeProcessor()

    # Process nodes
    print("\nProcessing nodes...")
    result = await processor.process_nodes(pages_data)

    if result["success"]:
        print("SUCCESS: Node processing thanh cong!")
        print(f"Total nodes: {result['summary']['total_nodes']}")
        print(f"Target nodes found: {result['summary']['target_nodes_found']}")
        print(f"Export ready: {result['summary']['export_ready_nodes']}")

        # Save reports
        print("\nSaving reports...")
        json_report, md_report = await processor.save_processor_report(result)

        print(f"JSON report: {json_report}")
        print(f"Markdown report: {md_report}")

        return True
    else:
        print(f"ERROR: Processing failed: {result.get('error')}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'Module 03 completed successfully' if success else 'Module 03 failed'}")
    sys.exit(0 if success else 1)