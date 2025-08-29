#!/usr/bin/env python3
"""
Test Figma File Structure và Page Count
=======================================

Script để verify Figma file structure và kiểm tra:
1. Số lượng pages thực tế
2. Node distribution trong mỗi page
3. Fetch logic với different depths
4. Target node IDs validation

Author: Kilo Code Debug Agent
Date: 2025-08-29
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import API client directly
import importlib.util
import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent / "scripts" / "modules"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Import API client module
api_spec = importlib.util.spec_from_file_location("api_client", scripts_dir / "02-api-client.py")
api_client = importlib.util.module_from_spec(api_spec)
api_spec.loader.exec_module(api_client)
FigmaApiClient = api_client.FigmaApiClient

async def test_file_structure(api_token: str, file_key: str) -> Dict[str, Any]:
    """Test Figma file structure với multiple depths"""

    print(f"[TEST] Testing Figma file structure for: {file_key}")
    print("=" * 80)

    async with FigmaApiClient(api_token) as client:
        results = {}

        # Test 1: Basic file info (depth=1)
        print("\n[TEST] 1. Fetching basic file info (depth=1)...")
        basic_result = await client.fetch_file_data(file_key, include_pages=True)

        if basic_result["success"]:
            print(f"[TEST] [OK] Basic fetch successful")
            print(f"[TEST]   File name: {basic_result['file_data']['name']}")
            print(f"[TEST]   Pages count: {basic_result['pages_count']}")
            results["basic_info"] = basic_result
        else:
            print(f"[TEST] [FAIL] Basic fetch failed: {basic_result.get('error')}")
            return {"success": False, "error": basic_result.get("error")}

        # Test 2: Pages with depth=2
        print("\n[TEST] 2. Fetching pages with depth=2...")
        pages_result = await client.fetch_file_pages(file_key)

        if pages_result["success"]:
            print(f"[TEST] [OK] Pages fetch successful")
            print(f"[TEST]   Total pages: {pages_result['total_pages']}")
            print(f"[TEST]   Total nodes: {pages_result['total_nodes']}")

            # Analyze each page
            for i, page in enumerate(pages_result["pages"]):
                print(f"[TEST]   Page {i+1}: {page['name']} (ID: {page['id']}) - {page['node_count']} nodes")

            results["pages_depth_2"] = pages_result
        else:
            print(f"[TEST] [FAIL] Pages fetch failed: {pages_result.get('error')}")
            results["pages_depth_2"] = pages_result

        # Test 3: Manual fetch with higher depth
        print("\n[TEST] 3. Testing manual fetch with depth=3...")
        try:
            url = f"{client.base_url}/files/{file_key}"
            params = {"depth": 3}

            manual_result = await client._make_request(url, params)

            if manual_result["success"]:
                data = manual_result["data"]
                document = data.get("document", {})
                children = document.get("children", [])

                print(f"[TEST] [OK] Manual fetch with depth=3 successful")
                print(f"[TEST]   Pages found: {len(children)}")

                # Analyze document structure
                for i, page in enumerate(children):
                    page_children = page.get("children", [])
                    print(f"[TEST]   Page {i+1}: {page.get('name')} - {len(page_children)} direct children")

                    # Check for nested children
                    total_nested = 0
                    for child in page_children:
                        if "children" in child:
                            total_nested += len(child.get("children", []))
                    print(f"[TEST]     Nested children: {total_nested}")

                results["manual_depth_3"] = {
                    "success": True,
                    "pages_count": len(children),
                    "pages": children
                }
            else:
                print(f"[TEST] [FAIL] Manual fetch failed: {manual_result.get('error')}")
                results["manual_depth_3"] = manual_result

        except Exception as e:
            print(f"[TEST] [FAIL] Manual fetch error: {str(e)}")
            results["manual_depth_3"] = {"success": False, "error": str(e)}

        # Test 4: Extract all node IDs
        print("\n[TEST] 4. Extracting all node IDs...")
        all_node_ids = []

        if results.get("manual_depth_3", {}).get("success"):
            pages = results["manual_depth_3"]["pages"]

            for page in pages:
                page_id = page.get("id")
                page_name = page.get("name")
                print(f"[TEST]   Processing page: {page_name} (ID: {page_id})")

                # Extract nodes from page
                page_nodes = extract_nodes_from_page(page)
                all_node_ids.extend(page_nodes)

                print(f"[TEST]     Found {len(page_nodes)} nodes in page")

        results["all_node_ids"] = all_node_ids
        print(f"[TEST] [OK] Total unique nodes found: {len(set(all_node_ids))}")

        # Test 5: Validate target nodes
        print("\n[TEST] 5. Validating target nodes...")
        target_nodes = ["453:37", "453:43"]  # From config
        found_targets = []

        for node_id in target_nodes:
            if node_id in all_node_ids:
                found_targets.append(node_id)
                print(f"[TEST] [OK] Target node {node_id} found")
            else:
                print(f"[TEST] [FAIL] Target node {node_id} NOT found")

        results["target_nodes_validation"] = {
            "expected": target_nodes,
            "found": found_targets,
            "missing": [nid for nid in target_nodes if nid not in all_node_ids]
        }

        return {
            "success": True,
            "results": results,
            "summary": {
                "file_key": file_key,
                "pages_count": results.get("manual_depth_3", {}).get("pages_count", 0),
                "total_nodes": len(set(all_node_ids)),
                "target_nodes_found": len(found_targets),
                "target_nodes_missing": len(target_nodes) - len(found_targets)
            }
        }

def extract_nodes_from_page(page: Dict[str, Any]) -> List[str]:
    """Extract all node IDs from a page recursively"""
    node_ids = []

    def traverse_node(node: Dict[str, Any]):
        if "id" in node:
            node_ids.append(node["id"])

        if "children" in node:
            for child in node["children"]:
                traverse_node(child)

    traverse_node(page)
    return node_ids

async def main():
    """Main test function"""
    print("[TEST] FIGMA FILE STRUCTURE TEST")
    print("=" * 80)

    # Load environment variables
    try:
        import os
        import dotenv
        dotenv.load_dotenv()

        api_token = os.getenv('FIGMA_API_TOKEN')
        file_key = os.getenv('FIGMA_FILE_KEY', 'DtARqKAHRvv21xSHHheyui')  # From config

        if not api_token:
            print("[TEST] [FAIL] Missing FIGMA_API_TOKEN environment variable")
            return False

        print(f"[TEST] Using file key: {file_key}")

        # Run structure test
        result = await test_file_structure(api_token, file_key)

        if result["success"]:
            print("\n" + "=" * 80)
            print("[TEST] TEST SUMMARY")
            print("=" * 80)
            summary = result["summary"]
            print(f"[TEST] File: {summary['file_key']}")
            print(f"[TEST] Pages: {summary['pages_count']}")
            print(f"[TEST] Total nodes: {summary['total_nodes']}")
            print(f"[TEST] Target nodes found: {summary['target_nodes_found']}")
            print(f"[TEST] Target nodes missing: {summary['target_nodes_missing']}")

            # Save detailed results
            output_file = "test_figma_structure_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"[TEST] Detailed results saved to: {output_file}")
            return True
        else:
            print(f"[TEST] [FAIL] Test failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"[TEST] [FAIL] Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n[TEST] Test {'completed successfully' if success else 'failed'}")
    sys.exit(0 if success else 1)