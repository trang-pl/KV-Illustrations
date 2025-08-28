"""
Node ID Format Converter cho Figma API
Convert giữa các format khác nhau của Figma node IDs
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class NodeIdFormat:
    """Định nghĩa format của node ID"""
    pattern: str
    description: str
    example: str


class NodeIdConverter:
    """Converter cho Figma node ID formats"""

    # Các format phổ biến của Figma node IDs
    FORMATS = {
        "dash_format": NodeIdFormat(
            pattern=r"^\d+-\d+$",
            description="Dash format (e.g., 431-22256)",
            example="431-22256"
        ),
        "colon_format": NodeIdFormat(
            pattern=r"^\d+:\d+$",
            description="Colon format (e.g., 431:22256)",
            example="431:22256"
        ),
        "full_path": NodeIdFormat(
            pattern=r"^\d+(:\d+)+$",
            description="Full path format (e.g., 0:1:2:3)",
            example="0:1:2:3"
        ),
        "page_node": NodeIdFormat(
            pattern=r"^\d+:\d+$",
            description="Page node format (e.g., 0:1)",
            example="0:1"
        )
    }

    @classmethod
    def detect_format(cls, node_id: str) -> Optional[str]:
        """Detect format của node ID"""
        for format_name, format_info in cls.FORMATS.items():
            if re.match(format_info.pattern, node_id):
                return format_name
        return None

    @classmethod
    def convert_dash_to_colon(cls, node_id: str) -> str:
        """Convert từ dash format sang colon format"""
        if cls.detect_format(node_id) == "dash_format":
            return node_id.replace("-", ":")
        return node_id

    @classmethod
    def convert_colon_to_dash(cls, node_id: str) -> str:
        """Convert từ colon format sang dash format"""
        if cls.detect_format(node_id) == "colon_format":
            return node_id.replace(":", "-")
        return node_id

    @classmethod
    def get_alternative_formats(cls, node_id: str) -> List[str]:
        """Tạo list các alternative formats cho một node ID"""
        alternatives = [node_id]  # Include original

        format_type = cls.detect_format(node_id)

        if format_type == "dash_format":
            alternatives.append(cls.convert_dash_to_colon(node_id))
        elif format_type == "colon_format":
            alternatives.append(cls.convert_colon_to_dash(node_id))

        # Add common variations
        if ":" in node_id:
            # Try removing last segment for parent node
            parts = node_id.split(":")
            if len(parts) > 1:
                parent_id = ":".join(parts[:-1])
                alternatives.append(parent_id)

        # Add root node as fallback
        if "0:1" not in alternatives:
            alternatives.append("0:1")

        return list(set(alternatives))  # Remove duplicates

    @classmethod
    def validate_node_id(cls, node_id: str) -> Dict[str, Any]:
        """Validate và phân tích node ID"""
        format_type = cls.detect_format(node_id)

        return {
            "is_valid": format_type is not None,
            "format": format_type,
            "alternatives": cls.get_alternative_formats(node_id),
            "original": node_id
        }

    @classmethod
    def extract_node_coordinates(cls, node_id: str) -> Optional[Dict[str, int]]:
        """Extract page và node coordinates từ node ID"""
        if ":" not in node_id:
            return None

        parts = node_id.split(":")
        if len(parts) >= 2:
            try:
                return {
                    "page_id": int(parts[0]),
                    "node_id": int(parts[1]),
                    "full_path": [int(p) for p in parts]
                }
            except ValueError:
                return None

        return None


class FigmaNodeResolver:
    """Resolver để tìm node với multiple fallback strategies"""

    def __init__(self, api_client):
        self.api_client = api_client
        self.converter = NodeIdConverter()

    async def resolve_node_with_fallbacks(
        self,
        file_key: str,
        node_id: str,
        max_attempts: int = 5
    ) -> Optional[Dict]:
        """Resolve node với multiple fallback strategies"""

        # Get alternative formats
        alternative_ids = self.converter.get_alternative_formats(node_id)

        # Limit attempts
        attempt_ids = alternative_ids[:max_attempts]

        print(f"Trying to resolve node {node_id} with {len(attempt_ids)} alternatives:")
        for i, alt_id in enumerate(attempt_ids, 1):
            print(f"  {i}. {alt_id}")

        for attempt_id in attempt_ids:
            print(f"\nTrying node ID: {attempt_id}")

            try:
                node_data = await self.api_client.get_node_structure(file_key, attempt_id)

                if node_data:
                    print(f"SUCCESS: Node {attempt_id} found - {node_data.get('name', 'Unknown')}")
                    return {
                        "node_data": node_data,
                        "resolved_id": attempt_id,
                        "original_id": node_id,
                        "format_used": self.converter.detect_format(attempt_id)
                    }

            except Exception as e:
                print(f"ERROR with {attempt_id}: {str(e)}")
                continue

        print(f"FAILED: Could not resolve node {node_id} with any alternative format")
        return None

    async def smart_node_search(
        self,
        file_key: str,
        search_term: str,
        node_type: Optional[str] = None
    ) -> List[Dict]:
        """Smart search cho nodes dựa trên tên hoặc pattern"""

        # Get root structure để search
        root_data = await self.resolve_node_with_fallbacks(file_key, "0:1")
        if not root_data:
            return []

        root_node = root_data["node_data"]

        def search_in_node(node, path=""):
            results = []
            node_name = node.get("name", "").lower()
            current_path = f"{path}/{node_name}" if path else node_name

            # Check if matches search term
            if search_term.lower() in node_name:
                if not node_type or node.get("type") == node_type:
                    results.append({
                        "id": node.get("id"),
                        "name": node.get("name"),
                        "type": node.get("type"),
                        "path": current_path
                    })

            # Search in children
            for child in node.get("children", []):
                results.extend(search_in_node(child, current_path))

            return results

        return search_in_node(root_node)