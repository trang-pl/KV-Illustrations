#!/usr/bin/env python3
"""
Demo Script: Improved Fetch Mechanism with Node ID Format Conversion and Figma Plugin API Integration

This script demonstrates the new features:
1. Node ID format conversion (dash ↔ colon)
2. Fallback resolution strategy
3. Enhanced fetch with metadata
4. Plugin API integration
5. Smart node search
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import dotenv
dotenv.load_dotenv()

from server.services.figma_sync import FigmaAPIClient, FigmaSyncService
from server.services.figma_plugin_client import FigmaPluginClient, EnhancedFigmaSyncService
from server.utils.node_id_converter import NodeIdConverter
from config.settings import reload_settings

# Reload settings
reload_settings()


async def demo_node_id_conversion():
    """Demo node ID format conversion"""
    print("==> DEMO 1: NODE ID FORMAT CONVERSION")
    print("=" * 50)

    converter = NodeIdConverter()

    test_cases = [
        ("431-22256", "Dash format from diagnostic"),
        ("431:22256", "Colon format from debug"),
        ("0:1", "Root node format"),
        ("344:11", "Page node format"),
    ]

    for node_id, description in test_cases:
        print(f"\n[TEST] Testing: {node_id} ({description})")

        # Detect format
        format_type = converter.detect_format(node_id)
        print(f"   Format: {format_type}")

        # Get alternatives
        alternatives = converter.get_alternative_formats(node_id)
        print(f"   Alternatives: {alternatives}")

        # Extract coordinates
        coords = converter.extract_node_coordinates(node_id)
        if coords:
            print(f"   Coordinates: Page {coords['page_id']}, Node {coords['node_id']}")

        # Validate
        validation = converter.validate_node_id(node_id)
        print(f"   Valid: {validation['is_valid']}")


async def demo_fallback_resolution():
    """Demo fallback node resolution"""
    print("\n==> DEMO 2: FALLBACK NODE RESOLUTION")
    print("=" * 50)

    token = os.environ.get('FIGMA_API_TOKEN')
    file_key = os.environ.get('FIGMA_FILE_KEY')

    if not token or not file_key:
        print("[ERROR] Missing environment variables")
        return

    api_client = FigmaAPIClient(token)

    # Test problematic node IDs
    test_nodes = [
        "431-22256",  # Original problematic node
        "353-2712",   # Another problematic node
        "0:1",        # Root node (should always work)
    ]

    for node_id in test_nodes:
        print(f"\n[TARGET] Testing fallback for: {node_id}")

        try:
            resolved = await api_client.get_node_structure_with_fallback(file_key, node_id)

            if resolved:
                print("   [OK] SUCCESS!")
                print(f"      Original: {resolved['original_id']}")
                print(f"      Resolved: {resolved['resolved_id']}")
                print(f"      Format: {resolved.get('format_used')}")
                print(f"      Node: {resolved['node_data'].get('name', 'Unknown')}")
            else:
                print("   [ERROR] FAILED: No resolution found")

        except Exception as e:
            print(f"   [ERROR] ERROR: {e}")


async def demo_enhanced_fetch():
    """Demo enhanced fetch with metadata"""
    print("\n==> DEMO 3: ENHANCED FETCH WITH METADATA")
    print("=" * 50)

    token = os.environ.get('FIGMA_API_TOKEN')
    file_key = os.environ.get('FIGMA_FILE_KEY')

    if not token or not file_key:
        print("[ERROR] Missing environment variables")
        return

    api_client = FigmaAPIClient(token)

    test_node = "0:1"  # Root node for demo
    print(f"[SEARCH] Enhanced fetch for: {test_node}")

    try:
        enhanced_node = await api_client.get_node_with_enhanced_info(file_key, test_node)

        if enhanced_node:
            print("   [OK] SUCCESS: Enhanced data retrieved!")

            # Show basic info
            print(f"      Name: {enhanced_node.get('name', 'Unknown')}")
            print(f"      Type: {enhanced_node.get('type', 'Unknown')}")
            print(f"      Children: {len(enhanced_node.get('children', []))}")

            # Show enhanced metadata
            metadata = enhanced_node.get("_enhanced_metadata", {})
            print(f"      Original ID: {metadata.get('original_node_id')}")
            print(f"      Resolved ID: {metadata.get('resolved_node_id')}")
            print(f"      Format Used: {metadata.get('format_used')}")
            print(f"      Fetched At: {metadata.get('fetch_timestamp')}")

            # Show validation info
            validation = metadata.get('node_id_validation', {})
            print(f"      ID Valid: {validation.get('is_valid')}")
            print(f"      Alternatives: {len(validation.get('alternatives', []))}")

        else:
            print("   [ERROR] FAILED: Could not fetch enhanced data")

    except Exception as e:
        print(f"   [ERROR] ERROR: {e}")


async def demo_smart_search():
    """Demo smart node search"""
    print("\n==> DEMO 4: SMART NODE SEARCH")
    print("=" * 50)

    token = os.environ.get('FIGMA_API_TOKEN')
    file_key = os.environ.get('FIGMA_FILE_KEY')

    if not token or not file_key:
        print("[ERROR] Missing environment variables")
        return

    api_client = FigmaAPIClient(token)

    search_terms = ["button", "icon", "frame"]

    for term in search_terms:
        print(f"\n[SEARCH] Searching for: '{term}'")

        try:
            results = await api_client.smart_node_search(file_key, term)

            if results:
                print(f"   [OK] Found {len(results)} nodes:")
                for i, node in enumerate(results[:5], 1):  # Show first 5
                    print(f"      {i}. {node['id']}: {node['name']} ({node['type']})")
                    print(f"         Path: {node['path']}")
            else:
                print(f"   [EMPTY] No nodes found for '{term}'")

        except Exception as e:
            print(f"   [ERROR] Search error: {e}")


async def demo_plugin_enhanced_sync():
    """Demo plugin-enhanced sync"""
    print("\n==> DEMO 5: PLUGIN-ENHANCED SYNC")
    print("=" * 50)

    token = os.environ.get('FIGMA_API_TOKEN')
    file_key = os.environ.get('FIGMA_FILE_KEY')

    if not token or not file_key:
        print("[ERROR] Missing environment variables")
        return

    enhanced_service = EnhancedFigmaSyncService()

    # Test with root node
    test_node = "0:1"
    output_dir = f"./demo_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print(f"[SYNC] Plugin-enhanced sync for: {test_node}")
    print(f"[DIR] Output directory: {output_dir}")

    try:
        result = await enhanced_service.enhanced_process_sync(
            file_key=file_key,
            node_id=test_node,
            output_dir=output_dir,
            force_sync=False,  # Don't force to show change detection
            use_plugin_enhancement=True
        )

        print("   [OK] SUCCESS: Sync completed!")
        print(f"      Original Node: {result.get('original_node_id')}")
        print(f"      Resolved Node: {result.get('resolved_node_id')}")
        print(f"      Exportable Children: {result.get('exportable_children_count', 0)}")
        print(f"      Downloads: {result.get('successful_downloads', 0)}")
        print(f"      Plugin Enhanced: {result.get('plugin_enhanced', False)}")

    except Exception as e:
        print(f"   [ERROR] Sync error: {e}")


async def main():
    """Main demo function"""
    print("[START] IMPROVED FETCH MECHANISM DEMO")
    print("=" * 60)
    print("Demo new features of improved fetch mechanism:")
    print("1. Node ID format conversion")
    print("2. Fallback resolution strategy")
    print("3. Enhanced fetch with metadata")
    print("4. Smart node search")
    print("5. Plugin-enhanced sync")
    print("=" * 60)

    # Check environment
    token = os.environ.get('FIGMA_API_TOKEN')
    file_key = os.environ.get('FIGMA_FILE_KEY')

    print(f"[KEY] API Token: {'[OK] Set' if token else '[ERROR] Missing'}")
    print(f"[FILE] File Key: {'[OK] Set' if file_key else '[ERROR] Missing'}")

    if not token or not file_key:
        print("\n[ERROR] Cannot run demo without FIGMA_API_TOKEN and FIGMA_FILE_KEY")
        print("Please set these in your .env file")
        return 1

    try:
        # Run all demos
        await demo_node_id_conversion()
        await demo_fallback_resolution()
        await demo_enhanced_fetch()
        await demo_smart_search()
        await demo_plugin_enhanced_sync()

        print("\n" + "=" * 60)
        print("[SUCCESS] DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Improved fetch mechanism is ready to use!")
        print("\nMain features:")
        print("[OK] Node ID format conversion (dash ↔ colon)")
        print("[OK] Fallback resolution strategy")
        print("[OK] Enhanced fetch with metadata")
        print("[OK] Plugin API integration")
        print("[OK] Smart node search")
        print("[OK] Comprehensive error handling")

        return 0

    except KeyboardInterrupt:
        print("\n[STOP]  Demo stopped by user")
        return 0
    except Exception as e:
        print(f"\n[CRASH] Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)