#!/usr/bin/env python3
"""
Debug script to check specific node 353-2712
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import dotenv
dotenv.load_dotenv()

from server.services.figma_sync import FigmaAPIClient

async def check_node_353_2712():
    """Check if node 353-2712 can be retrieved"""
    token = os.environ.get('FIGMA_API_TOKEN')
    file_key = os.environ.get('FIGMA_FILE_KEY')

    if not token or not file_key:
        print("Missing FIGMA_API_TOKEN or FIGMA_FILE_KEY")
        return

    client = FigmaAPIClient(token)

    print(f"Checking node 353-2712...")
    node_data = await client.get_node_structure(file_key, "353-2712")

    if not node_data:
        print("Trying node 344:11 instead...")
        node_data = await client.get_node_structure(file_key, "344:11")

    if node_data:
        print("SUCCESS: Node 353-2712 retrieved successfully!")
        print(f"Name: {node_data.get('name', 'Unknown')}")
        print(f"Type: {node_data.get('type', 'Unknown')}")
        print(f"Children count: {len(node_data.get('children', []))}")

        # Check if it has exportable children
        exportable_types = ["COMPONENT", "INSTANCE", "FRAME", "GROUP"]
        exportable_children = []

        def find_exportable(node, path=""):
            node_type = node.get("type", "")
            node_name = node.get("name", "Unnamed")
            node_id = node.get("id", "")

            current_path = f"{path}/{node_name}" if path else node_name

            if node_type in exportable_types and node_id:
                bbox = node.get("absoluteBoundingBox", {})
                width = bbox.get("width", 0)
                height = bbox.get("height", 0)

                if width > 0 and height > 0 and width <= 2000 and height <= 2000:
                    exportable_children.append({
                        "id": node_id,
                        "name": node_name,
                        "type": node_type,
                        "path": current_path
                    })

            for child in node.get("children", []):
                find_exportable(child, current_path)

        find_exportable(node_data)
        print(f"Exportable children: {len(exportable_children)}")

        for child in exportable_children[:5]:  # Show first 5
            print(f"  - {child['id']}: {child['name']} ({child['type']})")

    else:
        print("FAILED: Could not retrieve node 353-2712")
        print("This might be due to:")
        print("1. Node doesn't exist")
        print("2. Permission issues")
        print("3. API error")

if __name__ == "__main__":
    asyncio.run(check_node_353_2712())