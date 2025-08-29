#!/usr/bin/env python3
"""
Figma Filter Debug Script
=========================

Focused debug script để test filter logic without Unicode printing issues.

Author: Kilo Code Debug Agent
Version: 1.0.0
Date: 2025-08-29
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import dotenv for environment loading
try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    print("[WARNING] python-dotenv not installed, using environment variables only")

# Import figma client directly
import importlib.util
spec = importlib.util.spec_from_file_location("figma_client", "scripts/modules/02-figma-client-v1.0.py")
figma_client_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figma_client_module)
FigmaClient = figma_client_module.FigmaClient

async def debug_filter_logic():
    """Debug filter logic without Unicode printing issues"""
    print("[DEBUG] FIGMA FILTER DEBUG SESSION")
    print("=" * 80)

    # Load credentials
    api_token = os.getenv('FIGMA_API_TOKEN')
    file_key = os.getenv('FIGMA_FILE_KEY')

    if not api_token or not file_key:
        print("[ERROR] Missing credentials")
        return False

    print(f"[CONFIG] File Key: {file_key}")

    try:
        async with FigmaClient(api_token) as client:
            # Fetch pages
            print("\n1. FETCHING PAGES...")
            pages_result = await client.fetch_file_pages(file_key)
            if not pages_result["success"]:
                print(f"[ERROR] Failed to fetch pages: {pages_result.get('error')}")
                return False

            print(f"[SUCCESS] Found {pages_result.get('total_pages', 0)} pages, {pages_result.get('total_nodes', 0)} nodes")

            # Count nodes with specific patterns without printing
            print("\n2. ANALYZING NODE PATTERNS...")

            svg_exporter_count = 0
            img_exporter_count = 0
            total_nodes_checked = 0

            for page in pages_result.get("pages", []):
                for node in page.visible_nodes:
                    total_nodes_checked += 1
                    node_name_lower = node.name.lower()

                    if 'svg_exporter_' in node_name_lower:
                        svg_exporter_count += 1
                        print(f"[FOUND] SVG_EXPORTER: '{node.name}' in page '{page.name}'")
                    elif 'img_exporter_' in node_name_lower:
                        img_exporter_count += 1
                        print(f"[FOUND] IMG_EXPORTER: '{node.name}' in page '{page.name}'")

            print("\n[PATTERN ANALYSIS]")
            print(f"  Total nodes checked: {total_nodes_checked}")
            print(f"  SVG exporter nodes: {svg_exporter_count}")
            print(f"  IMG exporter nodes: {img_exporter_count}")

            # Test filter with different patterns
            print("\n3. TESTING FILTER PATTERNS...")

            test_patterns = [
                ["svg_exporter_*"],
                ["img_exporter_*"],
                ["svg_exporter_*", "img_exporter_*"],
                ["*"],  # Match all
            ]

            for i, patterns in enumerate(test_patterns, 1):
                print(f"\n[TEST {i}] Pattern: {patterns}")
                try:
                    filtered_result = await client.filter_nodes_by_criteria(
                        pages_result,
                        include_patterns=patterns
                    )

                    print(f"  Result: {filtered_result.get('total_nodes', 0)} nodes matched")
                    print(f"  Pages: {filtered_result.get('total_pages', 0)}")

                    # Show matched pages
                    for page in filtered_result.get("pages", []):
                        print(f"    - {page.name}: {page.node_count} nodes")

                except Exception as e:
                    print(f"  [ERROR] Filter failed: {e}")

            print("\n4. CONCLUSION")
            print("=" * 50)

            if svg_exporter_count > 0 or img_exporter_count > 0:
                print("[SUCCESS] Found exporter nodes that should match filter patterns")
                print(f"  - SVG exporter nodes: {svg_exporter_count}")
                print(f"  - IMG exporter nodes: {img_exporter_count}")
                print("[RECOMMENDATION] Filter logic should work - investigate why empty results reported")
            else:
                print("[WARNING] No exporter nodes found in current file")
                print("[RECOMMENDATION] Check if file contains expected node naming patterns")

            return True

    except Exception as e:
        print(f"\n[FATAL] Debug session failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_filter_logic())
    print(f"\n[RESULT] {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)