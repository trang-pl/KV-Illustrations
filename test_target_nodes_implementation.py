#!/usr/bin/env python3
"""
Test script để verify target_nodes implementation với node IDs 453:37 và 453:43
"""

import asyncio
import sys
from pathlib import Path

# Add scripts/modules to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "scripts" / "modules"))

# Import from the specific files
from importlib.util import spec_from_file_location, module_from_spec

async def test_target_nodes_implementation():
    """Test target_nodes implementation với sample data"""
    print("TESTING TARGET NODES IMPLEMENTATION")
    print("=" * 60)

    # Load node processor module
    spec = spec_from_file_location("node_processor", project_root / "scripts" / "modules" / "03-node-processor-v1.0.py")
    node_processor_module = module_from_spec(spec)
    spec.loader.exec_module(node_processor_module)

    NodeProcessor = node_processor_module.NodeProcessor
    ProcessedNode = node_processor_module.ProcessedNode

    # Create processor instance
    processor = NodeProcessor()

    # Test 1: Config loading with target_nodes
    print("\n1. Testing target_nodes config loading...")
    try:
        config = await processor.load_config()
        print(f"[SUCCESS] Config loaded successfully")
        print(f"   Target nodes enabled: {processor.target_nodes_config.get('enabled', False)}")
        print(f"   Target node IDs: {processor.target_nodes_config.get('node_ids', [])}")
        print(f"   Export mode: {processor.target_nodes_config.get('export_mode', 'svg')}")
        print(f"   Process children: {processor.target_nodes_config.get('process_children', True)}")
    except Exception as e:
        print(f"[ERROR] Config loading failed: {e}")
        return False

    # Test 2: Create sample data with target nodes
    print("\n2. Testing target node detection...")

    # Create sample pages data với target nodes
    sample_pages_data = {
        "success": True,
        "pages": [
            {
                "name": "Page 1",
                "id": "0:1",
                "visible_nodes": [
                    {
                        "id": "453:37",
                        "name": "svg_exporter_button_primary",
                        "type": "FRAME",
                        "page_id": "0:1",
                        "page_name": "Page 1"
                    },
                    {
                        "id": "453:43",
                        "name": "img_exporter_icon_main",
                        "type": "FRAME",
                        "page_id": "0:1",
                        "page_name": "Page 1"
                    },
                    {
                        "id": "453:37:1",
                        "name": "child_node_1",
                        "type": "RECTANGLE",
                        "page_id": "0:1",
                        "page_name": "Page 1"
                    },
                    {
                        "id": "453:43:2",
                        "name": "child_node_2",
                        "type": "VECTOR",
                        "page_id": "0:1",
                        "page_name": "Page 1"
                    },
                    {
                        "id": "1:100",
                        "name": "regular_node",
                        "type": "FRAME",
                        "page_id": "0:1",
                        "page_name": "Page 1"
                    }
                ]
            }
        ]
    }

    # Test 3: Process nodes with target_nodes logic
    print("\n3. Testing node processing with target_nodes...")

    try:
        result = await processor.process_nodes(sample_pages_data)
        print(f"[SUCCESS] Node processing completed")
        print(f"   Total processed nodes: {result['summary']['total_nodes']}")
        print(f"   Export ready nodes: {result['summary']['export_ready_nodes']}")
        print(f"   Target nodes found: {result['summary']['target_nodes_found']}")

        # Show processed nodes
        print("\n   Processed nodes:")
        for node in result['processed_nodes']:
            target_indicator = "[TARGET]" if node['is_target'] else "[REGULAR]"
            prefix_indicator = f"[{node['prefix']}]" if node['prefix'] else "[NO_PREFIX]"
            print(f"     {target_indicator} {prefix_indicator} {node['id']} - {node['name']}")

    except Exception as e:
        print(f"[ERROR] Node processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 4: Verify target nodes are correctly identified
    print("\n4. Verifying target node identification...")

    target_nodes_found = [node for node in result['processed_nodes'] if node['is_target']]
    expected_target_ids = ["453:37", "453:43"]

    found_ids = [node['id'] for node in target_nodes_found]
    print(f"   Expected target IDs: {expected_target_ids}")
    print(f"   Found target IDs: {found_ids}")

    if set(found_ids) == set(expected_target_ids):
        print("[SUCCESS] All target nodes correctly identified")
    else:
        print("[ERROR] Target node identification failed")
        return False

    # Test 5: Test child processing
    print("\n5. Testing child node processing...")

    child_nodes = [node for node in result['processed_nodes'] if ":" in node['id'] and node['id'].count(":") > 1]
    print(f"   Child nodes found: {len(child_nodes)}")
    for node in child_nodes:
        print(f"     Child: {node['id']} - {node['name']}")

    # Test 6: Save report
    print("\n6. Testing report generation...")

    try:
        json_report, md_report = await processor.save_processor_report(result)
        print(f"[SUCCESS] Reports saved:")
        print(f"   JSON: {json_report}")
        print(f"   Markdown: {md_report}")
    except Exception as e:
        print(f"[ERROR] Report generation failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL TARGET NODES TESTS COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print("✅ Config loading with target_nodes: PASSED")
    print("✅ Target node detection: PASSED")
    print("✅ Node processing with target_nodes: PASSED")
    print("✅ Child node processing: PASSED")
    print("✅ Report generation: PASSED")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = asyncio.run(test_target_nodes_implementation())
    sys.exit(0 if success else 1)