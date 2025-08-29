#!/usr/bin/env python3
"""
Test script để verify refactored node processor
"""

import asyncio

import sys
from pathlib import Path

# Add scripts/modules to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "scripts" / "modules"))

# Import from the specific file
from importlib.util import spec_from_file_location, module_from_spec

# Load the module from file
spec = spec_from_file_location("node_processor", project_root / "scripts" / "modules" / "03-node-processor-v1.0.py")
node_processor_module = module_from_spec(spec)
spec.loader.exec_module(node_processor_module)

NodeProcessor = node_processor_module.NodeProcessor
ProcessedNode = node_processor_module.ProcessedNode

async def test_refactored_processor():
    """Test refactored node processor với sample data"""
    print("TESTING REFACTORED NODE PROCESSOR")
    print("=" * 50)

    # Create processor instance
    processor = NodeProcessor()

    # Test config loading
    print("\n1. Testing config loading...")
    try:
        config = await processor.load_config()
        print(f"[SUCCESS] Config loaded successfully")
        print(f"   Naming prefixes: {processor.naming_prefixes}")
    except Exception as e:
        print(f"[ERROR] Config loading failed: {e}")
        return False

    # Test prefix detection
    print("\n2. Testing prefix detection...")
    test_names = [
        "svg_exporter_button",
        "img_exporter_icon",
        "icon_exporter_logo",
        "regular_node_name",
        "unknown_prefix_test"
    ]

    for name in test_names:
        prefix, base_name = processor.detect_prefix(name)
        status = "[OK]" if prefix else "[NO]"
        print(f"   {status} '{name}' -> prefix: {prefix}, base: '{base_name}'")

    # Test duplicate handling
    print("\n3. Testing duplicate handling...")

    # Create sample nodes with duplicates
    sample_nodes = [
        ProcessedNode(id="1:100", name="svg_exporter_button", type="FRAME", page_id="0:1", page_name="Page 1",
                     prefix="svg_exporter", base_name="button", export_ready=True),
        ProcessedNode(id="1:200", name="svg_exporter_button", type="FRAME", page_id="0:1", page_name="Page 1",
                     prefix="svg_exporter", base_name="button", export_ready=True),
        ProcessedNode(id="1:50", name="img_exporter_icon", type="FRAME", page_id="0:1", page_name="Page 1",
                     prefix="img_exporter", base_name="icon", export_ready=True),
    ]

    filtered_nodes = processor.handle_duplicate_names(sample_nodes)
    print(f"   Original nodes: {len(sample_nodes)}")
    print(f"   After duplicate handling: {len(filtered_nodes)}")
    for node in filtered_nodes:
        print(f"   [KEPT] {node.id} - {node.name}")

    print("\n4. Testing node filtering...")
    mixed_nodes = [
        ProcessedNode(id="1:100", name="svg_exporter_button", type="FRAME", page_id="0:1", page_name="Page 1",
                     prefix="svg_exporter", base_name="button", export_ready=True),
        ProcessedNode(id="1:200", name="regular_node", type="FRAME", page_id="0:1", page_name="Page 1",
                     prefix=None, base_name="regular_node", export_ready=False),
        ProcessedNode(id="1:300", name="img_exporter_icon", type="FRAME", page_id="0:1", page_name="Page 1",
                     prefix="img_exporter", base_name="icon", export_ready=True),
    ]

    filtered_by_prefix = processor.filter_nodes_by_prefix(mixed_nodes)
    print(f"   Original nodes: {len(mixed_nodes)}")
    print(f"   After prefix filtering: {len(filtered_by_prefix)}")
    for node in filtered_by_prefix:
        print(f"   [FILTERED] {node.name} (prefix: {node.prefix})")

    print("\n[SUCCESS] ALL TESTS COMPLETED SUCCESSFULLY")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_refactored_processor())
    sys.exit(0 if success else 1)