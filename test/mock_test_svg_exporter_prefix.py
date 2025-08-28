#!/usr/bin/env python3
"""
Mock Test Export theo prefix "svg_exporter_"
Demo logic export hoạt động đúng mà không cần kết nối Figma API thực sự
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from server.services.figma_sync import FigmaSyncService
import dotenv

# Load environment variables (không cần cho mock)
dotenv.load_dotenv()


class MockFigmaAPIClient:
    """Mock client để giả lập Figma API responses"""

    def __init__(self, token: str):
        self.token = token

    async def get_file_info(self, file_key: str):
        """Mock file info response"""
        return {
            "name": "Mock Figma File",
            "version": "1.0.0",
            "lastModified": "2024-01-01T00:00:00Z"
        }

    async def get_node_structure(self, file_key: str, node_id: str):
        """Mock node structure với các nodes có prefix svg_exporter_"""
        return {
            "id": node_id,
            "name": "Root Frame",
            "type": "FRAME",
            "children": [
                {
                    "id": "1:1",
                    "name": "svg_exporter_icon_home",
                    "type": "COMPONENT",
                    "absoluteBoundingBox": {"width": 24, "height": 24}
                },
                {
                    "id": "1:2",
                    "name": "svg_exporter_button_primary",
                    "type": "COMPONENT",
                    "absoluteBoundingBox": {"width": 100, "height": 40}
                },
                {
                    "id": "1:3",
                    "name": "svg_exporter_logo",
                    "type": "COMPONENT",
                    "absoluteBoundingBox": {"width": 200, "height": 60}
                },
                {
                    "id": "1:4",
                    "name": "regular_component",
                    "type": "COMPONENT",
                    "absoluteBoundingBox": {"width": 50, "height": 50}
                },
                {
                    "id": "1:5",
                    "name": "temp_draft",
                    "type": "COMPONENT",
                    "absoluteBoundingBox": {"width": 30, "height": 30}
                }
            ]
        }

    async def export_svg_batch(self, file_key: str, node_ids: list):
        """Mock SVG export URLs"""
        urls = {}
        for node_id in node_ids:
            urls[node_id] = f"https://mock-figma.com/images/{node_id}.svg"
        return urls

    async def download_svg_content(self, svg_url: str):
        """Mock SVG content download"""
        # Mock SVG content với fill đỏ và stroke đen
        return """<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 2L13.09 8.26L20 9L14 14.74L15.18 22L12 17.77L8.82 22L10 14.74L4 9L10.91 8.26L12 2Z"
        fill="#FF0000" stroke="#000000" stroke-width="1"/>
</svg>"""

    def sanitize_filename(self, name: str) -> str:
        """Giữ nguyên logic sanitize filename"""
        import re
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "_")
        name = name.lower().replace(" ", "-")
        name = re.sub(r"[-_]+", "-", name)
        name = name.strip("-_")
        if len(name) > 100:
            name = name[:100].rstrip("-_")
        return name or "unnamed"


async def test_mock_svg_exporter_prefix():
    """Mock test export voi prefix svg_exporter_"""
    print("Mock Test Export theo prefix 'svg_exporter_'")
    print("=" * 60)

    # Mock file key
    file_key = "mock_file_key_123"

    print(f"Mock File Key: {file_key}")

    # Create output directory for test
    output_dir = "./test/exports/svg_exporter_test"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Mock FigmaSyncService
    with patch('server.services.figma_sync.FigmaAPIClient', MockFigmaAPIClient):
        service = FigmaSyncService()

        # Root node ID default
        root_node_id = "0:1"

        try:
            # Run sync voi filter prefix svg_exporter_
            result = await service.process_sync(
                file_key=file_key,
                node_id=root_node_id,
                output_dir=output_dir,
                force_sync=True,  # Force sync to export all
                naming_filters={
                    "include_patterns": ["svg_exporter_*"],
                    "exclude_patterns": ["temp_*", "draft_*"],
                    "case_sensitive": False
                }
            )

            print("\nMock test export theo prefix 'svg_exporter_' completed!")
            print(f"Result: {result}")

            # Check results
            if result.get('exported', 0) > 0:
                print(f"Success: Exported {result['exported']} files voi prefix 'svg_exporter_'")

                # Display list of files
                output_path = Path(output_dir)
                if output_path.exists():
                    svg_files = list(output_path.rglob("*.svg"))
                    if svg_files:
                        print(f"\nExported files ({len(svg_files)} files):")
                        for i, svg_file in enumerate(svg_files[:10], 1):
                            size = svg_file.stat().st_size
                            print(f"   {i}. {svg_file.name} ({size} bytes)")

                        if len(svg_files) > 10:
                            print(f"   ... and {len(svg_files) - 10} more files")

                        # Verify SVG content has red fill and black stroke
                        print("\nVerifying SVG content...")
                        for svg_file in svg_files[:3]:  # Check first 3 files
                            with open(svg_file, 'r') as f:
                                content = f.read()
                                if 'fill="#FF0000"' in content and 'stroke="#000000"' in content:
                                    print(f"   {svg_file.name}: Has red fill and black stroke")
                                else:
                                    print(f"   {svg_file.name}: Missing expected colors")
            else:
                print("WARNING: No files exported voi prefix 'svg_exporter_'")
                print("   Possible reasons:")
                print("   - Filter logic not working")
                print("   - Mock data has no nodes with this prefix")

            return True

        except Exception as e:
            print(f"Error running mock test export: {e}")
            import traceback
            traceback.print_exc()
            return False


async def demo_mock_data():
    """Demo mock data structure"""
    print("\nDemo Mock Data Structure")
    print("=" * 40)

    mock_client = MockFigmaAPIClient("mock_token")

    # Show mock node structure
    structure = await mock_client.get_node_structure("mock_key", "0:1")
    print("Mock Node Structure:")
    for child in structure.get("children", []):
        name = child.get("name")
        is_svg_exporter = name.startswith("svg_exporter_")
        status = "MATCH" if is_svg_exporter else "SKIP"
        print(f"   {status} {name}")

    # Show mock SVG content
    svg_content = await mock_client.download_svg_content("mock_url")
    print(f"\nMock SVG Content Preview (first 200 chars):")
    print(svg_content[:200] + "...")


if __name__ == "__main__":
    print("Running Mock Test for SVG Exporter Prefix Logic")
    print("=" * 50)

    # Run demo mock data first
    asyncio.run(demo_mock_data())

    # Run mock test
    success = asyncio.run(test_mock_svg_exporter_prefix())
    sys.exit(0 if success else 1)