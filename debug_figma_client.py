#!/usr/bin/env python3
"""
Figma Client Debug Script
=========================

Comprehensive debug script để analyze figma-client module issues.
Tests API connectivity, page processing, và filter logic với detailed logging.

Author: Kilo Code Debug Agent
Version: 1.0.0
Date: 2025-08-29
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import dotenv for environment loading
try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    print("[WARNING] [WARNING] python-dotenv not installed, using environment variables only")

# Import figma client directly from file
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts', 'modules'))

# Import the module directly
import importlib.util
spec = importlib.util.spec_from_file_location("figma_client", "scripts/modules/02-figma-client-v1.0.py")
figma_client_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figma_client_module)
FigmaClient = figma_client_module.FigmaClient

async def debug_figma_client():
    """Debug Figma client với comprehensive logging"""
    print("[DEBUG] FIGMA CLIENT DEBUG SESSION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    # Load credentials
    api_token = os.getenv('FIGMA_API_TOKEN')
    file_key = os.getenv('FIGMA_FILE_KEY')

    if not api_token:
        print("[ERROR] FIGMA_API_TOKEN not found in environment")
        return False

    if not file_key:
        print("[ERROR] FIGMA_FILE_KEY not found in environment")
        return False

    print(f"[CONFIG] API Token: {api_token[:10]}... (length: {len(api_token)})")
    print(f"[CONFIG] File Key: {file_key}")
    print()

    try:
        async with FigmaClient(api_token) as client:
            print("[DEBUG] TESTING BASIC FILE DATA FETCH")
            print("-" * 50)

            # Test 1: Basic file data fetch
            file_result = await client.fetch_file_data(file_key, include_pages=False)
            if not file_result["success"]:
                print(f"[ERROR] [TEST 1] Failed: {file_result.get('error')}")
                return False

            print("[DEBUG] [TEST 1] Basic file data fetch successful")
            print(f"   File Name: {file_result.get('file_data', {}).get('name', 'Unknown')}")
            print(f"   Pages Count: {file_result.get('pages_count', 0)}")
            print()

            print("[DEBUG] TESTING DETAILED PAGE FETCH")
            print("-" * 50)

            # Test 2: Detailed page fetch
            pages_result = await client.fetch_file_pages(file_key)
            if not pages_result["success"]:
                print(f"[ERROR] [TEST 2] Failed: {pages_result.get('error')}")
                return False

            print("[DEBUG] [TEST 2] Page fetch successful")
            print(f"   Total Pages: {pages_result.get('total_pages', 0)}")
            print(f"   Total Nodes: {pages_result.get('total_nodes', 0)}")
            print()

            # Show page details
            for page in pages_result.get("pages", []):
                print(f"   [DEBUG] Page: {page.name} (ID: {page.id})")
                print(f"      Nodes: {page.node_count}")
                if page.visible_nodes:
                    print("      Sample nodes:")
                    for i, node in enumerate(page.visible_nodes[:3]):
                        print(f"        {i+1}. {node.name} (Type: {node.type})")
                print()

            print("[DEBUG] TESTING FILTER LOGIC")
            print("-" * 50)

            # Test 3a: Default filter (svg_exporter_*)
            print("[DEBUG] [FILTER TEST] Testing default filter: svg_exporter_*")
            filtered_result = await client.filter_nodes_by_criteria(
                pages_result,
                include_patterns=["svg_exporter_*"]
            )

            print(f"[DEBUG] [FILTER TEST] Default filter result:")
            print(f"   Filtered Pages: {filtered_result.get('total_pages', 0)}")
            print(f"   Filtered Nodes: {filtered_result.get('total_nodes', 0)}")
            print()

            # Test 3b: No filter (show all nodes)
            print("[DEBUG] [FILTER TEST] Testing no filter (show all nodes)")
            no_filter_result = await client.filter_nodes_by_criteria(
                pages_result,
                include_patterns=None
            )

            print(f"[DEBUG] [FILTER TEST] No filter result:")
            print(f"   Total Pages: {no_filter_result.get('total_pages', 0)}")
            print(f"   Total Nodes: {no_filter_result.get('total_nodes', 0)}")
            print()

            # Test 3c: Test different patterns
            test_patterns = [
                "svg_exporter_*",
                "img_exporter_*",
                "*",  # Match all
                "button",  # Common UI element
                "icon",    # Common UI element
            ]

            print("[DEBUG] [FILTER TEST] Testing different patterns:")
            for pattern in test_patterns:
                test_result = await client.filter_nodes_by_criteria(
                    pages_result,
                    include_patterns=[pattern]
                )
                print(f"   Pattern '{pattern}': {test_result.get('total_nodes', 0)} nodes")
            print()

            print("[DEBUG] GENERATING DEBUG REPORT")
            print("-" * 50)

            # Save debug report
            debug_report = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "test_results": {
                    "file_fetch": file_result,
                    "pages_fetch": pages_result,
                    "default_filter": filtered_result,
                    "no_filter": no_filter_result
                },
                "findings": {
                    "total_pages_found": pages_result.get("total_pages", 0),
                    "total_nodes_found": pages_result.get("total_nodes", 0),
                    "nodes_after_default_filter": filtered_result.get("total_nodes", 0),
                    "filter_efficiency": f"{filtered_result.get('total_nodes', 0)}/{pages_result.get('total_nodes', 0)}"
                }
            }

            # Save to file
            import json
            debug_file = f"debug_figma_client_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(debug_report, f, indent=2, ensure_ascii=False, default=str)

            print(f"[DEBUG] [REPORT] Debug report saved to: {debug_file}")
            print()

            print("[DEBUG] DEBUG SESSION SUMMARY")
            print("=" * 80)
            print("[DEBUG] API Connectivity: SUCCESS")
            print(f"[DEBUG] Pages Found: {pages_result.get('total_pages', 0)}")
            print(f"[DEBUG] Total Nodes: {pages_result.get('total_nodes', 0)}")
            print(f"[DEBUG] Filtered Nodes: {filtered_result.get('total_nodes', 0)}")

            if filtered_result.get('total_nodes', 0) == 0 and pages_result.get('total_nodes', 0) > 0:
                print("[WARNING] [WARNING] Filter returned 0 nodes despite having source nodes!")
                print("   This indicates filter pattern mismatch or node naming issues.")
            elif filtered_result.get('total_nodes', 0) > 0:
                print("[DEBUG] Filter working correctly - found matching nodes.")
            else:
                print("[ERROR] No nodes found at all - check API connectivity and file access.")

            return True

    except Exception as e:
        print(f"\n[ERROR] [FATAL] Debug session failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_figma_client())
    print(f"\n[DEBUG] Debug session {'completed successfully' if success else 'failed'}")
    sys.exit(0 if success else 1)