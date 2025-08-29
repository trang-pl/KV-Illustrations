#!/usr/bin/env python3
"""
Simple Node Processor Test with Real Figma Data
==============================================

Direct test of node processing functionality with real data.

Author: DS Tools - Simple Test
Date: 2025-08-29
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def load_figma_client_data():
    """Load data from Figma client report"""
    print("[DATA] Loading Figma client data...")

    data_file = Path("exports/figma_client/figma_client_report.json")

    if not data_file.exists():
        print(f"[ERROR] Figma client data file not found: {data_file}")
        return None

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"[SUCCESS] Loaded data with {data.get('total_nodes', 0)} nodes from {data.get('total_pages', 0)} pages")
    return data

def create_simple_node_objects(pages_data):
    """Create simple node objects from pages data"""
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

def extract_prefix_suffix(node_name):
    """Extract prefix and suffix from node name"""
    prefix = None
    suffix = None
    base_name = node_name

    # Extract prefix
    prefix_patterns = [
        r"^(svg_exporter_)",
        r"^(img_exporter_)",
        r"^(icon_)",
        r"^(illustration_)",
        r"^(ready_)",
        r"^(approved_)"
    ]

    import re
    for pattern in prefix_patterns:
        match = re.match(pattern, node_name, re.IGNORECASE)
        if match:
            prefix = match.group(1).rstrip("_")
            base_name = re.sub(pattern, "", node_name)
            break

    # Extract suffix
    suffix_patterns = [
        r"(_rasterized)$",
        r"(_vector)$",
        r"(_thumbnail)$",
        r"(_preview)$",
        r"(_final)$"
    ]

    for pattern in suffix_patterns:
        match = re.search(pattern, base_name, re.IGNORECASE)
        if match:
            suffix = match.group(1).lstrip("_")
            base_name = re.sub(pattern, "", base_name)
            break

    return prefix, suffix, base_name.strip()

def calculate_naming_score(node_name, prefix, suffix):
    """Calculate naming convention score (0-100)"""
    score = 0
    max_score = 100

    # Base score for having a name
    if node_name:
        score += 20

    # Bonus for having prefix
    if prefix:
        score += 30

    # Bonus for having suffix
    if suffix:
        score += 20

    # Bonus for following naming pattern
    if prefix and suffix:
        score += 20

    # Penalty for special characters (except underscore)
    import re
    special_chars = re.findall(r'[^a-zA-Z0-9_]', node_name)
    if special_chars:
        score -= len(special_chars) * 5

    # Penalty for very short names
    if len(node_name) < 3:
        score -= 10

    return max(0, min(max_score, score))

def validate_node(node_name, node_type):
    """Validate node properties and return list of errors"""
    errors = []

    # Check node name
    if not node_name or node_name.strip() == "":
        errors.append("Empty node name")

    if len(node_name) > 100:
        errors.append("Node name too long (>100 characters)")

    # Check for invalid characters
    import re
    invalid_chars = re.findall(r'[<>:"/\\|?*]', node_name)
    if invalid_chars:
        errors.append(f"Invalid characters found: {', '.join(invalid_chars)}")

    # Check node type
    valid_types = ["FRAME", "GROUP", "COMPONENT", "INSTANCE", "RECTANGLE",
                  "ELLIPSE", "POLYGON", "STAR", "VECTOR", "TEXT"]
    if node_type.upper() not in valid_types:
        errors.append(f"Unsupported node type: {node_type}")

    return errors

async def process_nodes_simple(pages_data, target_node_ids=None):
    """Simple node processing function"""
    print("[PROCESS] Starting simple node processing...")
    print("=" * 80)

    if not pages_data.get("success", False):
        return {
            "success": False,
            "error": "Invalid pages data provided",
            "processed_nodes": []
        }

    start_time = datetime.now(timezone.utc)
    processed_nodes = []
    target_found = []

    # Process each page
    for page in pages_data.get("pages", []):
        print(f"[PAGE] Processing page: {page.name} ({len(page.visible_nodes)} nodes)")

        for node in page.visible_nodes:
            # Extract prefix and suffix
            prefix, suffix, base_name = extract_prefix_suffix(node.name)

            # Calculate naming score
            naming_score = calculate_naming_score(node.name, prefix, suffix)

            # Validate node
            validation_errors = validate_node(node.name, node.type)

            # Check if target node
            is_target = False
            if target_node_ids and node.id in target_node_ids:
                is_target = True
                target_found.append(node.id)

            # Transform name if needed
            transformed_name = None
            if validation_errors:
                if node.name.startswith("svg_exporter_"):
                    transformed_name = node.name
                else:
                    transformed_name = f"svg_exporter_{node.name}"

            # Determine export readiness
            export_ready = (
                len(validation_errors) == 0 and
                naming_score >= 50 and
                prefix is not None
            )

            # Create processed node
            processed_node = {
                "id": node.id,
                "name": node.name,
                "type": node.type,
                "page_id": node.page_id,
                "page_name": node.page_name,
                "prefix": prefix,
                "suffix": suffix,
                "base_name": base_name,
                "naming_score": naming_score,
                "is_target": is_target,
                "validation_errors": validation_errors,
                "transformed_name": transformed_name,
                "export_ready": export_ready
            }

            processed_nodes.append(processed_node)

    end_time = datetime.now(timezone.utc)
    processing_time = (end_time - start_time).total_seconds()

    # Compile results
    result = {
        "success": True,
        "processed_nodes": processed_nodes,
        "summary": {
            "total_nodes": len(processed_nodes),
            "export_ready_nodes": len([n for n in processed_nodes if n["export_ready"]]),
            "target_nodes_found": len(target_found),
            "validation_errors": sum(len(n["validation_errors"]) for n in processed_nodes),
            "average_naming_score": sum(n["naming_score"] for n in processed_nodes) / len(processed_nodes) if processed_nodes else 0,
            "processing_time": processing_time
        },
        "target_nodes": target_found,
        "timestamp": start_time.isoformat()
    }

    print("[SUCCESS] Node processing completed")
    print(f"[SUMMARY] Total nodes: {result['summary']['total_nodes']}")
    print(f"[SUMMARY] Export ready: {result['summary']['export_ready_nodes']}")
    print(f"[SUMMARY] Target nodes found: {result['summary']['target_nodes_found']}")

    return result

async def save_simple_report(result, output_dir="exports/node_processor/"):
    """Save simple processing report"""
    print("[REPORT] Saving simple processing report...")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save detailed report
    report_file = output_path / "simple_node_processor_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Save summary report
    summary_file = output_path / "simple_node_processor_summary.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# Simple Node Processor Report\n\n")
        f.write(f"**Timestamp:** {result.get('timestamp', 'N/A')}\n\n")

        if result.get("success"):
            summary = result.get("summary", {})
            f.write("## Processing Successful\n\n")
            f.write(f"- **Total Nodes:** {summary.get('total_nodes', 0)}\n")
            f.write(f"- **Export Ready:** {summary.get('export_ready_nodes', 0)}\n")
            f.write(f"- **Target Nodes Found:** {summary.get('target_nodes_found', 0)}\n")
            f.write(f"- **Validation Errors:** {summary.get('validation_errors', 0)}\n")
            f.write(f"- **Average Naming Score:** {summary.get('average_naming_score', 0):.1f}%\n")
            f.write(f"- **Processing Time:** {summary.get('processing_time', 0):.2f} seconds\n\n")

            # Target nodes section
            target_nodes = result.get("target_nodes", [])
            if target_nodes:
                f.write("## Target Nodes Identified\n\n")
                for node_id in target_nodes:
                    f.write(f"- `{node_id}`\n")
                f.write("\n")

        else:
            f.write("## Processing Failed\n\n")
            f.write(f"**Error:** {result.get('error', 'Unknown error')}\n\n")

    print(f"[SUCCESS] Reports saved to: {output_path}")
    return str(report_file), str(summary_file)

async def main():
    """Main test function"""
    print("SIMPLE NODE PROCESSOR TEST")
    print("=" * 80)
    print("Testing node processing with real Figma data")
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
        pages_data = create_simple_node_objects(raw_data)

        # Step 3: Process nodes
        print("\n[STEP 3] Processing nodes...")
        target_node_ids = ["431:22256"]  # svg_exporter_thumbnail-rasterized
        result = await process_nodes_simple(pages_data, target_node_ids)

        # Step 4: Save reports
        print("\n[STEP 4] Saving reports...")
        report_file, summary_file = await save_simple_report(result)

        # Step 5: Display results
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
                    print(f"      {status}{target} {node.get('name')} (Score: {node.get('naming_score')})")

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

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\nTest {'completed successfully' if success else 'failed'}")
    sys.exit(0 if success else 1)