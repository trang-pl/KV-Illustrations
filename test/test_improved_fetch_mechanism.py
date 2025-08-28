#!/usr/bin/env python3
"""
Test Script for Improved Fetch Mechanism
Test node ID conversion và enhanced fetch capabilities
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dotenv
dotenv.load_dotenv()

from server.services.figma_sync import FigmaAPIClient, FigmaSyncService
from server.services.figma_plugin_client import FigmaPluginClient, EnhancedFigmaSyncService
from server.utils.node_id_converter import NodeIdConverter, FigmaNodeResolver
from config.settings import reload_settings

# Reload settings
reload_settings()


class ImprovedFetchMechanismTester:
    """Test class cho improved fetch mechanism"""

    def __init__(self):
        self.token = os.environ.get('FIGMA_API_TOKEN')
        self.file_key = os.environ.get('FIGMA_FILE_KEY')

        if not self.token or not self.file_key:
            raise ValueError("Missing FIGMA_API_TOKEN or FIGMA_FILE_KEY")

        # Initialize clients
        self.api_client = FigmaAPIClient(self.token)
        self.plugin_client = FigmaPluginClient(self.token)
        self.enhanced_service = EnhancedFigmaSyncService()
        self.node_converter = NodeIdConverter()

    async def test_node_id_conversion(self):
        """Test node ID format conversion"""
        print("\n" + "="*60)
        print("TEST 1: NODE ID FORMAT CONVERSION")
        print("="*60)

        test_cases = [
            "431-22256",  # Dash format
            "431:22256",  # Colon format
            "0:1",        # Root format
            "344:11",     # Another colon format
            "353-2712",   # Another dash format
        ]

        for node_id in test_cases:
            print(f"\nTesting node ID: {node_id}")

            # Test format detection
            format_type = self.node_converter.detect_format(node_id)
            print(f"  Detected format: {format_type}")

            # Test validation
            validation = self.node_converter.validate_node_id(node_id)
            print(f"  Is valid: {validation['is_valid']}")
            print(f"  Alternatives: {validation['alternatives']}")

            # Test coordinate extraction
            coords = self.node_converter.extract_node_coordinates(node_id)
            if coords:
                print(f"  Coordinates: Page {coords['page_id']}, Node {coords['node_id']}")

    async def test_fallback_resolution(self):
        """Test fallback node resolution"""
        print("\n" + "="*60)
        print("TEST 2: FALLBACK NODE RESOLUTION")
        print("="*60)

        test_node_ids = ["431-22256", "353-2712", "invalid-node-id"]

        for node_id in test_node_ids:
            print(f"\nTesting fallback resolution for: {node_id}")

            resolved = await self.api_client.get_node_structure_with_fallback(self.file_key, node_id)

            if resolved:
                print(f"  ✓ SUCCESS: Resolved to {resolved['resolved_id']}")
                print(f"    Original: {resolved['original_id']}")
                print(f"    Format used: {resolved.get('format_used')}")
                print(f"    Node name: {resolved['node_data'].get('name', 'Unknown')}")
            else:
                print(f"  ✗ FAILED: Could not resolve {node_id}")

    async def test_enhanced_node_fetch(self):
        """Test enhanced node fetching với metadata"""
        print("\n" + "="*60)
        print("TEST 3: ENHANCED NODE FETCH")
        print("="*60)

        test_node_ids = ["431-22256", "0:1"]  # Test with problematic and root nodes

        for node_id in test_node_ids:
            print(f"\nTesting enhanced fetch for: {node_id}")

            enhanced_node = await self.api_client.get_node_with_enhanced_info(self.file_key, node_id)

            if enhanced_node:
                print("  ✓ SUCCESS: Enhanced node data retrieved")
                metadata = enhanced_node.get("_enhanced_metadata", {})
                print(f"    Original ID: {metadata.get('original_node_id')}")
                print(f"    Resolved ID: {metadata.get('resolved_node_id')}")
                print(f"    Format used: {metadata.get('format_used')}")
                print(f"    Node name: {enhanced_node.get('name', 'Unknown')}")
                print(f"    Node type: {enhanced_node.get('type', 'Unknown')}")
                print(f"    Children count: {len(enhanced_node.get('children', []))}")
            else:
                print(f"  ✗ FAILED: Could not fetch enhanced data for {node_id}")

    async def test_plugin_enhanced_sync(self):
        """Test plugin-enhanced sync"""
        print("\n" + "="*60)
        print("TEST 4: PLUGIN-ENHANCED SYNC")
        print("="*60)

        # Test with root node first
        test_node_id = "0:1"
        output_dir = f"./test/exports/improved_fetch_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print(f"Testing plugin-enhanced sync for node: {test_node_id}")
        print(f"Output directory: {output_dir}")

        try:
            result = await self.enhanced_service.enhanced_process_sync(
                file_key=self.file_key,
                node_id=test_node_id,
                output_dir=output_dir,
                force_sync=True,
                use_plugin_enhancement=True
            )

            print("  ✓ SUCCESS: Plugin-enhanced sync completed")
            print(f"    Original node ID: {result.get('original_node_id')}")
            print(f"    Resolved node ID: {result.get('resolved_node_id')}")
            print(f"    Exportable children: {result.get('exportable_children_count', 0)}")
            print(f"    Successful downloads: {result.get('successful_downloads', 0)}")
            print(f"    Plugin enhanced: {result.get('plugin_enhanced', False)}")

        except Exception as e:
            print(f"  ✗ FAILED: Plugin-enhanced sync error: {e}")

    async def test_smart_node_search(self):
        """Test smart node search"""
        print("\n" + "="*60)
        print("TEST 5: SMART NODE SEARCH")
        print("="*60)

        search_terms = ["button", "icon", "logo"]

        for term in search_terms:
            print(f"\nSearching for nodes containing: '{term}'")

            try:
                results = await self.api_client.smart_node_search(self.file_key, term)

                if results:
                    print(f"  ✓ Found {len(results)} nodes:")
                    for i, node in enumerate(results[:3], 1):  # Show first 3
                        print(f"    {i}. {node['id']}: {node['name']} ({node['type']}) - {node['path']}")
                else:
                    print(f"  - No nodes found containing '{term}'")

            except Exception as e:
                print(f"  ✗ Search failed for '{term}': {e}")

    async def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print("IMPROVED FETCH MECHANISM COMPREHENSIVE TEST")
        print("="*80)
        print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"File key: {self.file_key}")
        print(f"Token available: {'YES' if self.token else 'NO'}")

        try:
            # Test 1: Node ID conversion
            await self.test_node_id_conversion()

            # Test 2: Fallback resolution
            await self.test_fallback_resolution()

            # Test 3: Enhanced node fetch
            await self.test_enhanced_node_fetch()

            # Test 4: Plugin-enhanced sync
            await self.test_plugin_enhanced_sync()

            # Test 5: Smart node search
            await self.test_smart_node_search()

            print("\n" + "="*80)
            print("COMPREHENSIVE TEST COMPLETED")
            print("="*80)

            return True

        except Exception as e:
            print(f"\nTEST SUITE ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main test function"""
    try:
        tester = ImprovedFetchMechanismTester()
        await tester.run_comprehensive_test()

    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please ensure FIGMA_API_TOKEN and FIGMA_FILE_KEY are set in .env file")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)