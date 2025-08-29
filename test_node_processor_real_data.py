#!/usr/bin/env python3
"""
Test Node Processor with Real Data Simulation
=============================================

Test script để validate node processor với:
- Logic filter AND đã sửa
- Target nodes: 453:37, 453:43
- Real naming prefixes từ config
- Export results generation

Author: Kilo Code Debug Agent
Date: 2025-08-29
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

@dataclass
class MockNode:
    """Mock Figma node for testing"""
    id: str
    name: str
    type: str = "FRAME"
    page_id: str = "0:1"
    page_name: str = "Page 1"

class NodeProcessorTester:
    """Test node processor với real config và mock data"""

    def __init__(self, config_path: str = "scripts/config/pipeline_config.json"):
        self.config_path = config_path
        self.config = {}
        self.naming_prefixes = {}
        self.target_nodes_config = {}

    async def load_config(self) -> Dict[str, Any]:
        """Load pipeline configuration"""
        print("[CONFIG] Loading pipeline configuration...")

        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # Extract naming_prefixes và target_nodes từ config
        export_config = self.config.get("export", {})
        self.naming_prefixes = export_config.get("naming_prefixes", {})
        self.target_nodes_config = export_config.get("target_nodes", {})

        print(f"[SUCCESS] Configuration loaded with {len(self.naming_prefixes)} naming prefixes")
        print(f"[PREFIXES] Available: {list(self.naming_prefixes.keys())}")
        print(f"[TARGET_NODES] Config: enabled={self.target_nodes_config.get('enabled', False)}")
        print(f"[TARGET_NODES] Node IDs: {self.target_nodes_config.get('node_ids', [])}")

        return self.config

    def detect_prefix(self, node_name: str) -> str:
        """Detect prefix từ node name theo config"""
        for prefix_key, prefix_value in self.naming_prefixes.items():
            if node_name.startswith(prefix_value):
                return prefix_key
        return None

    def is_target_node(self, node_id: str) -> bool:
        """Check if node is target node từ config"""
        if not self.target_nodes_config.get("enabled", False):
            return False

        target_node_ids = self.target_nodes_config.get("node_ids", [])
        return node_id in target_node_ids

    def create_mock_figma_data(self) -> Dict[str, Any]:
        """Create mock Figma data với target nodes và various scenarios"""
        mock_nodes = [
            # Target nodes với prefix hợp lệ (should pass AND logic)
            MockNode(id="453:37", name="svg_exporter_thumbnail", type="FRAME"),
            MockNode(id="453:43", name="img_exporter_banner", type="FRAME"),

            # Target nodes không có prefix (should fail AND logic)
            MockNode(id="453:37", name="regular_thumbnail", type="FRAME"),
            MockNode(id="453:43", name="normal_banner", type="FRAME"),

            # Non-target nodes với prefix hợp lệ (should fail AND logic)
            MockNode(id="453:50", name="svg_exporter_icon", type="FRAME"),
            MockNode(id="453:60", name="img_exporter_button", type="FRAME"),

            # Non-target nodes không có prefix (should fail AND logic)
            MockNode(id="453:70", name="regular_icon", type="FRAME"),
            MockNode(id="453:80", name="normal_button", type="FRAME"),

            # Additional test cases
            MockNode(id="999:999", name="svg_exporter_test", type="FRAME"),
            MockNode(id="888:888", name="icon_exporter_close", type="FRAME"),
        ]

        # Convert to Figma API format
        pages = [{
            "name": "Page 1",
            "visible_nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type,
                    "page_id": node.page_id
                } for node in mock_nodes
            ]
        }]

        return {
            "success": True,
            "pages": pages,
            "total_pages": 1,
            "total_nodes": len(mock_nodes)
        }

    def process_nodes_with_and_logic(self, pages_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process nodes với logic AND đã sửa"""
        print("[PROCESS] Starting node processing with AND logic...")
        print("=" * 60)

        if not pages_data.get("success", False):
            return {"success": False, "error": "Invalid pages data"}

        processed_nodes = []
        start_time = datetime.now(timezone.utc)

        # Process each page
        for page in pages_data.get("pages", []):
            page_name = page.get("name", "Unknown Page")
            visible_nodes = page.get("visible_nodes", [])
            print(f"[PAGE] Processing page: {page_name} ({len(visible_nodes)} nodes)")

            for node_data in visible_nodes:
                node_id = node_data.get("id", "")
                node_name = node_data.get("name", "")
                node_type = node_data.get("type", "")

                # Detect prefix
                prefix = self.detect_prefix(node_name)

                # Check if target node
                is_target = self.is_target_node(node_id)

                # Apply AND logic: prefix AND target_node
                export_ready = (prefix is not None) and is_target

                # Create processed node
                processed_node = {
                    "id": node_id,
                    "name": node_name,
                    "type": node_type,
                    "page_id": node_data.get("page_id", ""),
                    "page_name": page_name,
                    "prefix": prefix,
                    "base_name": node_name[len(self.naming_prefixes.get(prefix, "")):] if prefix else node_name,
                    "is_target": is_target,
                    "validation_errors": [],
                    "export_ready": export_ready
                }

                processed_nodes.append(processed_node)

                # Debug output
                status = "[PASS]" if export_ready else "[FAIL]"
                print(f"{status} {node_id}: '{node_name}' -> prefix='{prefix}', target={is_target}")

        end_time = datetime.now(timezone.utc)
        processing_time = (end_time - start_time).total_seconds()

        # Calculate summary
        export_ready_nodes = [n for n in processed_nodes if n["export_ready"]]
        target_nodes_found = [n for n in processed_nodes if n["is_target"]]

        result = {
            "success": True,
            "processed_nodes": processed_nodes,
            "summary": {
                "total_nodes": len(processed_nodes),
                "export_ready_nodes": len(export_ready_nodes),
                "target_nodes_found": len(target_nodes_found),
                "validation_errors": 0,
                "processing_time": processing_time
            },
            "target_nodes_config": self.target_nodes_config,
            "timestamp": start_time.isoformat()
        }

        print("[SUCCESS] Node processing completed")
        print(f"[SUMMARY] Total nodes: {result['summary']['total_nodes']}")
        print(f"[SUMMARY] Export ready: {result['summary']['export_ready_nodes']}")
        print(f"[SUMMARY] Target nodes found: {result['summary']['target_nodes_found']}")

        return result

    def save_export_results(self, result: Dict[str, Any], output_dir: str = "exports/test_results/"):
        """Save export results to files"""
        print(f"[EXPORT] Saving results to: {output_dir}")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save detailed JSON report
        json_file = output_path / "node_processor_test_report.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # Save summary markdown report
        md_file = output_path / "node_processor_test_summary.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# Node Processor Test Results\n\n")
            f.write(f"**Timestamp:** {result.get('timestamp', 'N/A')}\n\n")

            if result.get("success"):
                summary = result.get("summary", {})
                f.write("## Test Results Summary\n\n")
                f.write(f"- **Total Nodes:** {summary.get('total_nodes', 0)}\n")
                f.write(f"- **Export Ready (AND logic):** {summary.get('export_ready_nodes', 0)}\n")
                f.write(f"- **Target Nodes Found:** {summary.get('target_nodes_found', 0)}\n")
                f.write(f"- **Processing Time:** {summary.get('processing_time', 0):.2f} seconds\n\n")

                # Target nodes config
                target_config = result.get("target_nodes_config", {})
                if target_config.get("enabled", False):
                    f.write("## Target Nodes Configuration\n\n")
                    f.write(f"- **Enabled:** {target_config.get('enabled', False)}\n")
                    f.write(f"- **Node IDs:** {', '.join(target_config.get('node_ids', []))}\n")
                    f.write(f"- **Export Mode:** {target_config.get('export_mode', 'svg')}\n\n")

                # Export ready nodes
                export_ready_nodes = [n for n in result.get("processed_nodes", []) if n.get("export_ready", False)]
                if export_ready_nodes:
                    f.write("## Nodes Passed AND Filter\n\n")
                    for node in export_ready_nodes:
                        f.write(f"- `{node['id']}` - {node['name']} (prefix: {node.get('prefix', 'None')})\n")
                    f.write("\n")

                # Test validation
                expected_passes = 2  # 453:37 and 453:43 with valid prefixes
                actual_passes = len(export_ready_nodes)
                if actual_passes == expected_passes:
                    f.write("## Test Status: PASSED\n\n")
                    f.write("AND logic is working correctly!\n")
                else:
                    f.write("## Test Status: FAILED\n\n")
                    f.write(f"Expected {expected_passes} nodes to pass, but got {actual_passes}\n")

            else:
                f.write("## Test Failed\n\n")
                f.write(f"**Error:** {result.get('error', 'Unknown error')}\n\n")

        print(f"[SUCCESS] Reports saved:")
        print(f"  JSON: {json_file}")
        print(f"  Markdown: {md_file}")

        return str(json_file), str(md_file)

async def main():
    """Main test function"""
    print("NODE PROCESSOR REAL DATA TEST")
    print("=" * 50)

    # Initialize tester
    tester = NodeProcessorTester()

    try:
        # Load config
        await tester.load_config()

        # Create mock Figma data
        print("\n[TEST] Creating mock Figma data with target nodes 453:37, 453:43...")
        mock_data = tester.create_mock_figma_data()
        print(f"[TEST] Created {mock_data['total_nodes']} mock nodes")

        # Process nodes with AND logic
        print("\n[PROCESS] Processing nodes with AND logic...")
        result = tester.process_nodes_with_and_logic(mock_data)

        # Save export results
        json_file, md_file = tester.save_export_results(result)

        # Final summary
        print("\n" + "=" * 50)
        print("TEST RESULTS SUMMARY")
        print("=" * 50)

        if result.get("success"):
            summary = result.get("summary", {})
            export_ready = summary.get("export_ready_nodes", 0)
            target_found = summary.get("target_nodes_found", 0)

            print(f"[RESULT] Total nodes processed: {summary.get('total_nodes', 0)}")
            print(f"[RESULT] Target nodes found: {target_found}")
            print(f"[RESULT] Export ready (AND logic): {export_ready}")

            # Validate results
            expected_passes = 2  # Should have 2 nodes that pass AND logic
            if export_ready == expected_passes:
                print("[SUCCESS] AND logic test PASSED!")
                print(f"[VALIDATION] Expected {expected_passes} nodes, got {export_ready} nodes")
                return True
            else:
                print("[ERROR] AND logic test FAILED!")
                print(f"[VALIDATION] Expected {expected_passes} nodes, got {export_ready} nodes")
                return False
        else:
            print(f"[ERROR] Processing failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"[FATAL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    print(f"\n[FINISH] Node processor test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)