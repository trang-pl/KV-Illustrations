#!/usr/bin/env python3
"""
Test script to verify all 02-* sub modules can be imported correctly
"""

import importlib.util
import sys
from pathlib import Path

def test_imports():
    """Test importing all sub modules"""
    print("Testing 02-* sub modules imports...")

    # Add current directory to path
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))

    try:
        # Test 1: Import config_manager
        print("1. Testing 02-config-manager.py...")
        config_spec = importlib.util.spec_from_file_location("config_manager", current_dir / "02-config-manager.py")
        config_manager = importlib.util.module_from_spec(config_spec)
        config_spec.loader.exec_module(config_manager)
        ConfigManager = config_manager.ConfigManager
        print("   [OK] 02-config-manager.py imported successfully")

        # Test 2: Import api_client
        print("2. Testing 02-api-client.py...")
        api_spec = importlib.util.spec_from_file_location("api_client", current_dir / "02-api-client.py")
        api_client = importlib.util.module_from_spec(api_spec)
        api_spec.loader.exec_module(api_client)
        FigmaApiClient = api_client.FigmaApiClient
        print("   [OK] 02-api-client.py imported successfully")

        # Test 3: Import filter_engine
        print("3. Testing 02-filter-engine.py...")
        filter_spec = importlib.util.spec_from_file_location("filter_engine", current_dir / "02-filter-engine.py")
        filter_engine = importlib.util.module_from_spec(filter_spec)
        filter_spec.loader.exec_module(filter_engine)
        FilterEngine = filter_engine.FilterEngine
        print("   [OK] 02-filter-engine.py imported successfully")

        # Test 4: Import report_generator
        print("4. Testing 02-report-generator.py...")
        report_spec = importlib.util.spec_from_file_location("report_generator", current_dir / "02-report-generator.py")
        report_generator = importlib.util.module_from_spec(report_spec)
        report_spec.loader.exec_module(report_generator)
        ReportGenerator = report_generator.ReportGenerator
        print("   [OK] 02-report-generator.py imported successfully")

        # Test 5: Test main module imports
        print("5. Testing main module with sub modules...")
        main_spec = importlib.util.spec_from_file_location("figma_client", current_dir / "02-figma-client-fixed-v1.0.py")
        main_module = importlib.util.module_from_spec(main_spec)
        main_spec.loader.exec_module(main_module)
        print("   [OK] Main module imported successfully with all sub modules")

        print("\n[SUCCESS] ALL TESTS PASSED!")
        print("All 02-* sub modules have been successfully restored and are working correctly.")
        return True

    except Exception as e:
        print(f"\n[FAILED] IMPORT TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)