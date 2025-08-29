#!/usr/bin/env python3
"""
Node Processor Module v1.0 - Refactored
=======================================

Simplified node processor theo yêu cầu mới:

✅ Đã loại bỏ scoring system
✅ Detect prefix theo config (không hardcode)
✅ Filter nodes có prefix hợp lệ để export
✅ Rule trùng tên: chọn 1 node duy nhất theo index
✅ Bỏ suffix detection
✅ Sử dụng config đúng cách từ config files

Cấu trúc logic mới:
1. Load config với naming_prefixes
2. Detect prefix từ config
3. Filter nodes có prefix hợp lệ
4. Handle duplicate names theo index
5. Return filtered nodes cho export

Author: DS Tools - Modular Pipeline
Version: 1.0.1
Date: 2025-08-29
"""

import re
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class ProcessedNode:
    """Represents a processed node với prefix detection"""
    id: str
    name: str
    type: str
    page_id: str
    page_name: str
    prefix: Optional[str] = None
    base_name: str = ""
    is_target: bool = False
    validation_errors: List[str] = None
    export_ready: bool = False

    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []

class NodeProcessor:
    """Simplified node processor theo yêu cầu mới"""

    def __init__(self, config_path: Optional[str] = None, config_manager=None):
        # Use figma_client_config.json as default
        self.config_path = config_path or "scripts/config/figma_client_config.json"
        # Adjust path if running from modules directory
        if not Path(self.config_path).exists():
            self.config_path = "../config/figma_client_config.json"
        self.config_manager = config_manager
        self.naming_prefixes = {}  # Load từ config
        self.target_nodes = []
        self.target_nodes_config = {}  # Store target_nodes config
        self.processed_nodes = []

    async def load_config(self) -> Dict[str, Any]:
        """Load figma_client configuration và extract naming_prefixes và target_nodes"""
        print("[CONFIG] Loading figma_client configuration...")

        # Try to use config_manager first if available
        if self.config_manager:
            self.naming_prefixes = self.config_manager.get_naming_prefixes()._asdict()
            self.target_nodes_config = self.config_manager.get_target_nodes()._asdict()
            print(f"[SUCCESS] Configuration loaded from config_manager with {len(self.naming_prefixes)} naming prefixes")
            print(f"[PREFIXES] Available: {list(self.naming_prefixes.keys())}")
            print(f"[TARGET_NODES] Config loaded: enabled={self.target_nodes_config.get('enabled', False)}")
            return {"naming_prefixes": self.naming_prefixes, "target_nodes": self.target_nodes_config}

        # Fallback to loading from file
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Extract naming_prefixes từ config mới
        self.naming_prefixes = config.get("naming_prefixes", {})

        # Extract target_nodes config từ config mới
        self.target_nodes_config = config.get("target_nodes", {})

        print(f"[SUCCESS] Configuration loaded with {len(self.naming_prefixes)} naming prefixes")
        print(f"[PREFIXES] Available: {list(self.naming_prefixes.keys())}")
        print(f"[TARGET_NODES] Config loaded: enabled={self.target_nodes_config.get('enabled', False)}")

        return config

    def detect_prefix(self, node_name: str) -> Tuple[Optional[str], str]:
        """Detect prefix từ node name theo config"""
        # Check từng prefix trong config
        for prefix_key, prefix_value in self.naming_prefixes.items():
            if node_name.startswith(prefix_value):
                base_name = node_name[len(prefix_value):].strip()
                return prefix_key, base_name

        # Không có prefix hợp lệ
        return None, node_name

    def handle_duplicate_names(self, nodes: List[ProcessedNode]) -> List[ProcessedNode]:
        """Handle duplicate names bằng cách chọn node theo index"""
        print("[DUPLICATE] Handling duplicate names...")

        # Group by base_name
        name_groups = {}
        for node in nodes:
            if node.base_name not in name_groups:
                name_groups[node.base_name] = []
            name_groups[node.base_name].append(node)

        # Filter duplicates - chỉ giữ lại node đầu tiên trong mỗi group
        filtered_nodes = []
        duplicates_removed = 0

        for base_name, node_list in name_groups.items():
            if len(node_list) > 1:
                # Sort by index (giả sử node.id chứa index)
                try:
                    sorted_nodes = sorted(node_list, key=lambda x: int(x.id.split(':')[1]) if ':' in x.id else 0)
                except (ValueError, IndexError):
                    sorted_nodes = node_list

                # Chọn node đầu tiên (thấp nhất index)
                filtered_nodes.append(sorted_nodes[0])
                duplicates_removed += len(node_list) - 1
                print(f"[DUPLICATE] Removed {len(node_list) - 1} duplicates for '{base_name}'")
            else:
                filtered_nodes.append(node_list[0])

        print(f"[DUPLICATE] Total duplicates removed: {duplicates_removed}")
        return filtered_nodes

    def validate_node(self, node_name: str, node_type: str) -> List[str]:
        """Validate node properties và return list of errors"""
        errors = []

        # Check node name
        if not node_name or node_name.strip() == "":
            errors.append("Empty node name")

        if len(node_name) > 100:
            errors.append("Node name too long (>100 characters)")

        # Check for invalid characters
        invalid_chars = re.findall(r'[<>:"/\\|?*]', node_name)
        if invalid_chars:
            errors.append(f"Invalid characters found: {', '.join(invalid_chars)}")

        # Check node type
        valid_types = ["FRAME", "GROUP", "COMPONENT", "INSTANCE", "RECTANGLE",
                      "ELLIPSE", "POLYGON", "STAR", "VECTOR", "TEXT"]
        if node_type.upper() not in valid_types:
            errors.append(f"Unsupported node type: {node_type}")

        return errors

    def filter_nodes_by_prefix(self, nodes: List[ProcessedNode]) -> List[ProcessedNode]:
        """Filter nodes có prefix hợp lệ từ config"""
        print("[FILTER] Filtering nodes by prefix...")

        filtered_nodes = []
        for node in nodes:
            if node.prefix is not None:  # Chỉ lấy nodes có prefix hợp lệ
                filtered_nodes.append(node)

        print(f"[FILTER] Filtered {len(filtered_nodes)} nodes with valid prefixes")
        return filtered_nodes

    def get_filtered_nodes_for_export(self, pages_data: Dict[str, Any]) -> List[ProcessedNode]:
        """Main method để filter nodes cho export theo yêu cầu mới với target_nodes support"""
        print("[PROCESS] Starting simplified node processing...")

        if not pages_data.get("success", False):
            return []

        # Load config (đã được load trong __init__ hoặc process_nodes)
        config = {"export": {"target_nodes": self.target_nodes_config}}

        processed_nodes = []

        # Process each page
        for page in pages_data.get("pages", []):
            page_name = page.get("name", "Unknown Page")
            visible_nodes = page.get("visible_nodes", [])
            print(f"[PAGE] Processing page: {page_name} ({len(visible_nodes)} nodes)")

            for node in visible_nodes:
                # Detect prefix theo config
                node_name = node.get("name", "")
                node_id = node.get("id", "")
                node_type = node.get("type", "")

                prefix, base_name = self.detect_prefix(node_name)

                # Validate node
                validation_errors = self.validate_node(node_name, node_type)

                # Check if target node (support both old and new config)
                is_target = self._is_target_node(node_id, config)

                # Determine export readiness - có prefix hợp lệ VÀ là target node (AND logic)
                export_ready = (
                    len(validation_errors) == 0 and
                    (prefix is not None and is_target)
                )

                # Create processed node
                processed_node = ProcessedNode(
                    id=node_id,
                    name=node_name,
                    type=node_type,
                    page_id=node.get("page_id", ""),
                    page_name=page_name,
                    prefix=prefix,
                    base_name=base_name,
                    is_target=is_target,
                    validation_errors=validation_errors,
                    export_ready=export_ready
                )

                processed_nodes.append(processed_node)

        # Apply target_nodes filtering if enabled
        if self.target_nodes_config.get("enabled", False):
            processed_nodes = self._filter_target_nodes(processed_nodes, pages_data)

        # Filter nodes có prefix hợp lệ (hoặc target nodes)
        filtered_nodes = self.filter_nodes_by_prefix(processed_nodes)

        # Handle duplicate names
        final_nodes = self.handle_duplicate_names(filtered_nodes)

        print(f"[SUCCESS] Processing complete: {len(final_nodes)} nodes ready for export")
        return final_nodes

    def _is_target_node(self, node_id: str, config: Dict[str, Any]) -> bool:
        """Check if node is a target node from either old or new config"""
        # Check new target_nodes config
        if self.target_nodes_config.get("enabled", False):
            target_node_ids = self.target_nodes_config.get("node_ids", [])
            if node_id in target_node_ids:
                return True

        # Check old figma target_node config for backward compatibility
        old_target_node = config.get("figma", {}).get("target_node", "")
        if old_target_node:
            old_target_ids = [id.strip() for id in old_target_node.split(",")]
            if node_id in old_target_ids:
                return True

        return False

    def _filter_target_nodes(self, processed_nodes: List[ProcessedNode], pages_data: Dict[str, Any]) -> List[ProcessedNode]:
        """Filter and process target nodes with children if enabled"""
        print("[TARGET_NODES] Applying target nodes filtering...")

        target_node_ids = self.target_nodes_config.get("node_ids", [])
        process_children = self.target_nodes_config.get("process_children", True)
        export_mode = self.target_nodes_config.get("export_mode", "svg")

        print(f"[TARGET_NODES] Target node IDs: {target_node_ids}")
        print(f"[TARGET_NODES] Process children: {process_children}")
        print(f"[TARGET_NODES] Export mode: {export_mode}")

        filtered_nodes = []

        for node in processed_nodes:
            # Include target nodes
            if node.id in target_node_ids:
                filtered_nodes.append(node)
                print(f"[TARGET_NODES] Included target node: {node.id} ({node.name})")

                # Process children if enabled
                if process_children:
                    child_nodes = self._get_child_nodes(node.id, processed_nodes)
                    filtered_nodes.extend(child_nodes)
                    print(f"[TARGET_NODES] Added {len(child_nodes)} child nodes for {node.id}")

        print(f"[TARGET_NODES] Total nodes after target filtering: {len(filtered_nodes)}")
        return filtered_nodes

    def _get_child_nodes(self, parent_node_id: str, all_nodes: List[ProcessedNode]) -> List[ProcessedNode]:
        """Get child nodes of a parent node"""
        child_nodes = []

        # This is a simplified implementation
        # In a real Figma API, you'd need to traverse the node hierarchy
        # For now, we'll use a basic heuristic based on node IDs

        for node in all_nodes:
            # Simple heuristic: if node ID contains parent ID as prefix
            if node.id.startswith(parent_node_id + ":") or node.id.startswith(parent_node_id + "."):
                child_nodes.append(node)

        return child_nodes

    def _make_serializable(self, obj):
        """Convert dataclass objects to serializable dicts"""
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            # Convert dataclass or other objects with __dict__
            result = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):  # Skip private attributes
                    result[key] = self._make_serializable(value)
            return result
        else:
            return obj

    async def process_nodes(self, pages_data: Dict[str, Any],
                           target_node_ids: List[str] = None) -> Dict[str, Any]:
        """Main method to process nodes theo cấu trúc mới đơn giản"""
        print("[PROCESS] Starting simplified node processing...")
        print("=" * 80)

        if not pages_data.get("success", False):
            return {
                "success": False,
                "error": "Invalid pages data provided",
                "processed_nodes": []
            }

        start_time = datetime.now(timezone.utc)

        # Load config trước khi process
        config = await self.load_config()

        # Sử dụng method mới để filter nodes
        filtered_nodes = self.get_filtered_nodes_for_export(pages_data)

        end_time = datetime.now(timezone.utc)
        processing_time = (end_time - start_time).total_seconds()

        # Compile results theo cấu trúc mới với target_nodes info
        result = {
            "success": True,
            "processed_nodes": [asdict(node) for node in filtered_nodes],
            "summary": {
                "total_nodes": len(filtered_nodes),
                "export_ready_nodes": len([n for n in filtered_nodes if n.export_ready]),
                "target_nodes_found": len([n for n in filtered_nodes if n.is_target]),
                "validation_errors": sum(len(n.validation_errors) for n in filtered_nodes),
                "processing_time": processing_time
            },
            "target_nodes_config": self.target_nodes_config,
            "timestamp": start_time.isoformat()
        }

        print("[SUCCESS] Simplified node processing completed")
        print(f"[SUMMARY] Total nodes: {result['summary']['total_nodes']}")
        print(f"[SUMMARY] Export ready: {result['summary']['export_ready_nodes']}")
        print(f"[SUMMARY] Target nodes found: {result['summary']['target_nodes_found']}")

        return result

    async def filter_export_ready_nodes(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter chỉ export-ready nodes (giữ nguyên logic)"""
        print("[FILTER] Filtering export-ready nodes...")

        if not processed_data.get("success", False):
            return processed_data

        all_nodes = processed_data.get("processed_nodes", [])
        export_ready_nodes = [node for node in all_nodes if node.get("export_ready", False)]

        filtered_result = processed_data.copy()
        filtered_result["processed_nodes"] = export_ready_nodes
        filtered_result["summary"]["export_ready_nodes"] = len(export_ready_nodes)

        print(f"[SUCCESS] Filtered to {len(export_ready_nodes)} export-ready nodes")
        return filtered_result

    async def save_processor_report(self, result: Dict[str, Any],
                                   output_dir: str = "exports/node_processor/"):
        """Save node processor operation report"""
        print("[REPORT] Saving node processor report...")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Convert dataclass objects to dict for serialization
        serializable_result = self._make_serializable(result)

        # Save detailed report
        report_file = output_path / "node_processor_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, indent=2, ensure_ascii=False)

        # Save summary report
        summary_file = output_path / "node_processor_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# Node Processor Operation Summary\n\n")
            f.write(f"**Timestamp:** {result.get('timestamp', 'N/A')}\n\n")

            if result.get("success"):
                summary = result.get("summary", {})
                f.write("## ✅ Processing Successful\n\n")
                f.write(f"- **Total Nodes:** {summary.get('total_nodes', 0)}\n")
                f.write(f"- **Export Ready:** {summary.get('export_ready_nodes', 0)}\n")
                f.write(f"- **Target Nodes Found:** {summary.get('target_nodes_found', 0)}\n")
                f.write(f"- **Validation Errors:** {summary.get('validation_errors', 0)}\n")
                f.write(f"- **Processing Time:** {summary.get('processing_time', 0):.2f} seconds\n\n")

                # Target nodes section
                target_nodes_config = result.get("target_nodes_config", {})
                if target_nodes_config.get("enabled", False):
                    f.write("## 🎯 Target Nodes Configuration\n\n")
                    f.write(f"- **Enabled:** {target_nodes_config.get('enabled', False)}\n")
                    f.write(f"- **Node IDs:** {', '.join(target_nodes_config.get('node_ids', []))}\n")
                    f.write(f"- **Export Mode:** {target_nodes_config.get('export_mode', 'svg')}\n")
                    f.write(f"- **Process Children:** {target_nodes_config.get('process_children', True)}\n")
                    f.write("\n")

                    # Show target nodes found
                    target_nodes_found = [node for node in result.get("processed_nodes", []) if node.get("is_target", False)]
                    if target_nodes_found:
                        f.write("### Target Nodes Found\n\n")
                        for node in target_nodes_found:
                            f.write(f"- `{node['id']}` - {node['name']} ({node['type']})\n")
                        f.write("\n")

                # Recommendations
                f.write("## 💡 Recommendations\n\n")
                if summary.get('validation_errors', 0) > 0:
                    f.write("- Review and fix validation errors before export\n")
                if summary.get('target_nodes_found', 0) == 0:
                    f.write("- Verify target node IDs are correct\n")
                if summary.get('export_ready_nodes', 0) == 0:
                    f.write("- Check if nodes have valid prefixes from config\n")

            else:
                f.write("## ❌ Processing Failed\n\n")
                f.write(f"**Error:** {result.get('error', 'Unknown error')}\n\n")

        print(f"[SUCCESS] Reports saved to: {output_path}")
        return str(report_file), str(summary_file)

async def main():
    """Main function for standalone execution"""
    print("NODE PROCESSOR MODULE v1.0")
    print("=" * 80)
    print("Process nodes voi prefix extraction va validation")
    print()

    # For standalone execution, we would need to load data from previous modules
    # This is a placeholder for integration with the pipeline
    print("[INFO] This module is designed to work within the pipeline")
    print("[INFO] Use the pipeline orchestrator for full functionality")
    print()

    # Create sample data for testing
    sample_result = {
        "success": True,
        "processed_nodes": [],
        "summary": {
            "total_nodes": 0,
            "export_ready_nodes": 0,
            "target_nodes_found": 0,
            "validation_errors": 0,
            "processing_time": 0
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    processor = NodeProcessor()
    await processor.save_processor_report(sample_result)

    print("\n" + "=" * 80)
    print("NODE PROCESSOR SUMMARY")
    print("=" * 80)
    print("Status: Module loaded successfully")
    print("Use pipeline orchestrator for full processing")

    return True

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    print(f"\nNode processor {'completed successfully' if success else 'failed'}")

    sys.exit(0 if success else 1)