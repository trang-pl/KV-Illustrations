#!/usr/bin/env python3
"""
Test Script with Full Config using Node ID 353-2712 from Figma URL
Test both export modes: nodeID and prefix
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dotenv

# Load environment variables FIRST
dotenv.load_dotenv()

from server.services.figma_sync import FigmaSyncService
from config.settings import settings, reload_settings

# Reload settings after loading environment variables
reload_settings()

# Debug: Check if token is loaded
print(f"DEBUG: FIGMA_API_TOKEN from settings: {settings.figma.api_token}")
print(f"DEBUG: All figma settings: {settings.figma.model_dump()}")

# Test API connection first
import os
token = os.environ.get('FIGMA_API_TOKEN')
file_key = os.environ.get('FIGMA_FILE_KEY')
print(f"DEBUG: Using token: {token[:10]}...{token[-5:] if token else 'None'}")
print(f"DEBUG: Using file key: {file_key}")


class TestConfig:
    """Test configuration with full parameters"""

    def __init__(self):
        # Node ID from Figma URL - using root node since 353-2712 may not be directly accessible
        self.target_node_id = "0:1"  # Root node

        # Export config
        self.export_config = {
            "force_sync": True,
            "batch_size": settings.figma.batch_size,
            "delay_between_batches": settings.figma.delay_between_batches,
            "max_retries": settings.figma.max_retries,
            "retry_delay": settings.figma.retry_delay
        }

        # Naming filters for prefix mode
        self.prefix_filters = {
            "include_patterns": ["svg_exporter_*"],
            "exclude_patterns": ["temp_*", "draft_*"],
            "case_sensitive": False
        }

        # Output directories
        self.output_base = "./test/exports/node_353_2712_test"
        self.node_id_output = f"{self.output_base}/node_id_mode"
        self.prefix_output = f"{self.output_base}/prefix_mode"


async def test_node_id_mode(service: FigmaSyncService, config: TestConfig) -> dict:
    """Test export mode by specific node ID"""
    print("\n" + "="*70)
    print("TEST NODE ID MODE: 353-2712")
    print("="*70)

    # Get FIGMA_FILE_KEY from .env
    file_key = os.environ.get('FIGMA_FILE_KEY')
    if not file_key:
        print("FIGMA_FILE_KEY not found in .env")
        return {"error": "Missing FIGMA_FILE_KEY"}

    print(f"File Key: {file_key}")
    print(f"Node ID: {config.target_node_id}")
    print(f"Output: {config.node_id_output}")
    print(f"Config: force_sync={config.export_config['force_sync']}")

    try:
        # Run export with specific node ID
        result = await service.process_sync(
            file_key=file_key,
            node_id=config.target_node_id,
            output_dir=config.node_id_output,
            force_sync=config.export_config['force_sync']
        )

        print("\nNODE ID TEST RESULTS:")
        print(f"   • Exported: {result.get('exported', 0)}")
        print(f"   • Failed: {result.get('failed', 0)}")
        print(f"   • Skipped: {result.get('skipped', 0)}")
        print(f"   • Dev-ready: {result.get('dev_ready', 0)}")
        print(f"   • Needs review: {result.get('needs_review', 0)}")
        print(f"   • Time: {result.get('elapsed_time', 'N/A')}")

        return result

    except Exception as e:
        print(f"Error testing node ID mode: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


async def test_prefix_mode(service: FigmaSyncService, config: TestConfig) -> dict:
    """Test export mode by prefix"""
    print("\n" + "="*70)
    print("TEST PREFIX MODE: svg_exporter_*")
    print("="*70)

    # Get FIGMA_FILE_KEY from .env
    file_key = os.environ.get('FIGMA_FILE_KEY')
    if not file_key:
        print("FIGMA_FILE_KEY not found in .env")
        return {"error": "Missing FIGMA_FILE_KEY"}

    print(f"File Key: {file_key}")
    print(f"Prefix Filter: {config.prefix_filters['include_patterns']}")
    print(f"Exclude Patterns: {config.prefix_filters['exclude_patterns']}")
    print(f"Output: {config.prefix_output}")
    print(f"Config: force_sync={config.export_config['force_sync']}")

    try:
        # Run export with prefix filter
        result = await service.process_sync(
            file_key=file_key,
            node_id="0:1",  # Root node
            output_dir=config.prefix_output,
            force_sync=config.export_config['force_sync'],
            naming_filters=config.prefix_filters
        )

        print("\nPREFIX TEST RESULTS:")
        print(f"   • Exported: {result.get('exported', 0)}")
        print(f"   • Failed: {result.get('failed', 0)}")
        print(f"   • Skipped: {result.get('skipped', 0)}")
        print(f"   • Dev-ready: {result.get('dev_ready', 0)}")
        print(f"   • Needs review: {result.get('needs_review', 0)}")
        print(f"   • Time: {result.get('elapsed_time', 'N/A')}")

        return result

    except Exception as e:
        print(f"Error testing prefix mode: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def print_test_summary(results: dict, config: TestConfig):
    """Print test summary"""
    print("\n" + "="*80)
    print("SUMMARY TEST NODE 353-2712 - FULL CONFIG")
    print("="*80)
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output base: {config.output_base}")

    # Node ID mode results
    node_result = results.get('node_id', {})
    if 'error' not in node_result:
        print("\nNODE ID MODE:")
        print(f"   Success: {node_result.get('exported', 0)} files")
        print(f"   Failed: {node_result.get('failed', 0)} files")
        print(f"   Skipped: {node_result.get('skipped', 0)} files")
    else:
        print(f"   Error: {node_result['error']}")

    # Prefix mode results
    prefix_result = results.get('prefix', {})
    if 'error' not in prefix_result:
        print("\nPREFIX MODE:")
        print(f"   Success: {prefix_result.get('exported', 0)} files")
        print(f"   Failed: {prefix_result.get('failed', 0)} files")
        print(f"   Skipped: {prefix_result.get('skipped', 0)} files")
    else:
        print(f"   Error: {prefix_result['error']}")

    # Config used
    print("\nCONFIG USED:")
    print(f"   • Batch size: {config.export_config['batch_size']}")
    print(f"   • Delay between batches: {config.export_config['delay_between_batches']}s")
    print(f"   • Max retries: {config.export_config['max_retries']}")
    print(f"   • Force sync: {config.export_config['force_sync']}")

    # Check instructions
    print("\nCHECK INSTRUCTIONS:")
    print(f"   1. Node ID mode: {config.node_id_output}")
    print(f"   2. Prefix mode: {config.prefix_output}")
    print("   3. Check export_report.json for details")

    # Summary
    total_exported = (
        node_result.get('exported', 0) +
        prefix_result.get('exported', 0)
    )

    if total_exported > 0:
        print(f"\nTEST COMPLETED - Total {total_exported} files exported!")
    else:
        print("\nTEST COMPLETED - No files exported")


async def main():
    """Main test function"""
    print("START TEST NODE 353-2712 WITH FULL CONFIG")
    print("="*80)

    # Initialize config
    config = TestConfig()

    # Create output directories
    Path(config.node_id_output).mkdir(parents=True, exist_ok=True)
    Path(config.prefix_output).mkdir(parents=True, exist_ok=True)

    # Initialize service
    service = FigmaSyncService()

    # Run Node ID mode test
    node_result = await test_node_id_mode(service, config)

    # Run Prefix mode test
    prefix_result = await test_prefix_mode(service, config)

    # Combine results
    results = {
        'node_id': node_result,
        'prefix': prefix_result
    }

    # Print summary
    print_test_summary(results, config)

    # Return results
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        # Exit code based on results
        has_error = any('error' in str(result) for result in results.values())
        sys.exit(0 if not has_error else 1)
    except KeyboardInterrupt:
        print("\nTest stopped by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)