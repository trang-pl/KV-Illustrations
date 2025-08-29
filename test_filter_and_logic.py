#!/usr/bin/env python3
"""
Test Script for Filter AND Logic
================================

Test logic filter AND giữa prefix naming và target nodes:
- Node phải có prefix hợp lệ VÀ là target node
- Kết quả = (prefix naming filter) AND (target nodes filter)

Author: Kilo Code Debug Agent
Date: 2025-08-29
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class TestNode:
    """Test node representation"""
    id: str
    name: str
    type: str
    prefix: str = None
    is_target: bool = False
    export_ready: bool = False

class FilterLogicTester:
    """Test filter AND logic implementation"""

    def __init__(self):
        self.naming_prefixes = {
            "svg_exporter": "svg_exporter_",
            "img_exporter": "img_exporter_",
            "icon_exporter": "icon_exporter_"
        }
        self.target_node_ids = ["453:37", "453:43"]

    def detect_prefix(self, node_name: str) -> str:
        """Detect prefix từ node name"""
        for prefix_key, prefix_value in self.naming_prefixes.items():
            if node_name.startswith(prefix_value):
                return prefix_key
        return None

    def is_target_node(self, node_id: str) -> bool:
        """Check if node is target node"""
        return node_id in self.target_node_ids

    def apply_filter_and_logic(self, nodes: List[TestNode]) -> List[TestNode]:
        """Apply AND logic: prefix AND target_node"""
        print("[FILTER] Applying AND logic: (prefix) AND (target_node)")
        print(f"[CONFIG] Target nodes: {self.target_node_ids}")
        print(f"[CONFIG] Naming prefixes: {list(self.naming_prefixes.keys())}")

        filtered_nodes = []

        for node in nodes:
            # Detect prefix
            prefix = self.detect_prefix(node.name)
            node.prefix = prefix

            # Check if target node
            is_target = self.is_target_node(node.id)
            node.is_target = is_target

            # Apply AND logic: prefix AND target_node
            export_ready = (prefix is not None) and is_target
            node.export_ready = export_ready

            print(f"[NODE] {node.id}: '{node.name}' -> prefix='{prefix}', target={is_target}, export_ready={export_ready}")

            if export_ready:
                filtered_nodes.append(node)

        return filtered_nodes

def create_test_data() -> List[TestNode]:
    """Create test data với various scenarios"""
    return [
        # Case 1: Có prefix + là target node (should pass AND logic)
        TestNode(id="453:37", name="svg_exporter_thumbnail", type="FRAME"),

        # Case 2: Có prefix + không phải target node (should fail AND logic)
        TestNode(id="453:50", name="svg_exporter_icon", type="FRAME"),

        # Case 3: Không có prefix + là target node (should fail AND logic)
        TestNode(id="453:43", name="regular_thumbnail", type="FRAME"),

        # Case 4: Không có prefix + không phải target node (should fail AND logic)
        TestNode(id="453:60", name="regular_icon", type="FRAME"),

        # Case 5: Có prefix khác + là target node (should pass AND logic)
        TestNode(id="453:37", name="img_exporter_banner", type="FRAME"),

        # Case 6: Test với node ID không có trong target list
        TestNode(id="999:999", name="svg_exporter_test", type="FRAME"),
    ]

def main():
    """Main test function"""
    print("FILTER AND LOGIC TEST")
    print("=" * 50)

    # Initialize tester
    tester = FilterLogicTester()

    # Create test data
    test_nodes = create_test_data()
    print(f"\n[TEST] Testing with {len(test_nodes)} nodes:")
    for node in test_nodes:
        print(f"  - {node.id}: '{node.name}'")

    print("\n" + "-" * 50)

    # Apply filter AND logic
    filtered_nodes = tester.apply_filter_and_logic(test_nodes)

    print("\n" + "=" * 50)
    print("FILTER RESULTS")
    print("=" * 50)

    print(f"[RESULT] Total input nodes: {len(test_nodes)}")
    print(f"[RESULT] Filtered nodes (AND logic): {len(filtered_nodes)}")

    if filtered_nodes:
        print("\n[DETAIL] Nodes that passed AND filter:")
        for node in filtered_nodes:
            print(f"  [PASS] {node.id}: '{node.name}' (prefix='{node.prefix}', target={node.is_target})")
    else:
        print("\n[WARNING] No nodes passed the AND filter!")

    # Expected results analysis
    expected_passes = 2  # Case 1 and Case 5 should pass
    if len(filtered_nodes) == expected_passes:
        print(f"\n[SUCCESS] AND logic working correctly: {len(filtered_nodes)}/{len(test_nodes)} nodes passed")
        return True
    else:
        print(f"\n[ERROR] AND logic failed: Expected {expected_passes} passes, got {len(filtered_nodes)}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n[FINISH] Test {'PASSED' if success else 'FAILED'}")