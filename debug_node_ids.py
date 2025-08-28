#!/usr/bin/env python3
"""
Debug script to list all node IDs in Figma file
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

async def list_all_node_ids():
    """List all node IDs and names from root"""
    token = os.environ.get('FIGMA_API_TOKEN')
    file_key = os.environ.get('FIGMA_FILE_KEY')

    if not token or not file_key:
        print("Missing FIGMA_API_TOKEN or FIGMA_FILE_KEY")
        return

    client = FigmaAPIClient(token)

    print(f"Getting node structure for root: 0:1")
    root_node = await client.get_node_structure(file_key, "0:1")

    if not root_node:
        print("Failed to get root node structure")
        return

    def traverse_and_list(node, depth=0, path=""):
        node_id = node.get("id", "")
        node_name = node.get("name", "Unnamed")
        node_type = node.get("type", "")

        indent = "  " * depth
        # Handle Unicode characters
        try:
            print(f"{indent}{node_id}: {node_name} ({node_type})")
        except UnicodeEncodeError:
            safe_name = node_name.encode('utf-8', errors='replace').decode('utf-8')
            print(f"{indent}{node_id}: {safe_name} ({node_type})")

        for child in node.get("children", []):
            traverse_and_list(child, depth + 1, f"{path}/{node_name}")

    print("\nAll nodes in file:")
    print("=" * 50)
    traverse_and_list(root_node)

    # Also check if 353-2712 exists
    print("\n" + "=" * 50)
    print("Checking if 353-2712 exists...")
    node_353_2712 = await client.get_node_structure(file_key, "353-2712")
    if node_353_2712:
        print(f"Node 353-2712 found: {node_353_2712.get('name')} ({node_353_2712.get('type')})")
    else:
        print("Node 353-2712 NOT found or not accessible")

if __name__ == "__main__":
    asyncio.run(list_all_node_ids())