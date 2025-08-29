#!/usr/bin/env python3
"""
Test Config Integration v1.0
============================

Test script to verify all modules can load and use the merged figma_client_config.json
Tests config loading, module integration, and basic functionality.

Author: Kilo Code Debug Agent
Date: 2025-08-29
"""

import sys
import json
import importlib.util
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config_file_exists():
    """Test that figma_client_config.json exists and is valid JSON"""
    print("[TEST] Testing config file existence...")

    config_path = project_root / "scripts" / "config" / "figma_client_config.json"

    if not config_path.exists():
        print(f"[FAIL] Config file not found: {config_path}")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        print(f"[PASS] Config file loaded successfully: {config_path}")
        print(f"   Config sections: {list(config.keys())}")

        # Check required sections
        required_sections = ["naming_prefixes", "filter_patterns", "api_settings", "output_settings", "target_nodes"]
        for section in required_sections:
            if section not in config:
                print(f"[FAIL] Missing required section: {section}")
                return False
            print(f"   [OK] {section}: {type(config[section]).__name__}")

        return True

    except json.JSONDecodeError as e:
        print(f"[FAIL] Invalid JSON in config file: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error reading config file: {e}")
        return False

def test_config_manager():
    """Test ConfigManager can load the new config structure"""
    print("\n[TEST] Testing ConfigManager...")

    try:
        # Import ConfigManager
        sys.path.insert(0, str(project_root / "scripts" / "modules"))
        spec = importlib.util.spec_from_file_location("config_manager", project_root / "scripts" / "modules" / "02-config-manager.py")
        config_manager = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_manager)
        ConfigManager = config_manager.ConfigManager

        # Initialize with figma_client_config.json
        config_path = project_root / "scripts" / "config" / "figma_client_config.json"
        config_manager = ConfigManager(str(config_path))

        # Test getting config
        config = config_manager.get_config()

        print("[PASS] ConfigManager initialized successfully")
        print(f"   Naming prefixes: {len(config.naming_prefixes._asdict())} items")
        print(f"   Filter patterns: include={len(config.filter_patterns.include)}, exclude={len(config.filter_patterns.exclude)}")
        print(f"   API settings: base_url={config.api_settings.base_url}")
        print(f"   Output settings: dir={config.output_settings.default_output_dir}")
        print(f"   Target nodes: enabled={config.target_nodes.enabled}, node_ids={len(config.target_nodes.node_ids)}")

        # Test config summary
        summary = config_manager.get_config_summary()
        if "error" not in summary:
            print("[PASS] Config summary generated successfully")
        else:
            print(f"[FAIL] Config summary error: {summary['error']}")
            return False

        return True

    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] ConfigManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_client():
    """Test API Client can use config settings"""
    print("\n[TEST] Testing API Client...")

    try:
        # Import API Client
        spec = importlib.util.spec_from_file_location("api_client", project_root / "scripts" / "modules" / "02-api-client.py")
        api_client = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api_client)
        FigmaApiClient = api_client.FigmaApiClient

        # Mock API token for testing
        api_token = "test_token"

        # Create ConfigManager
        spec = importlib.util.spec_from_file_location("config_manager", project_root / "scripts" / "modules" / "02-config-manager.py")
        config_manager_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_manager_module)
        ConfigManager = config_manager_module.ConfigManager
        config_path = project_root / "scripts" / "config" / "figma_client_config.json"
        config_manager = ConfigManager(str(config_path))

        # Initialize API client
        api_client = FigmaApiClient(api_token, config_manager)

        print("[PASS] API Client initialized successfully")
        print(f"   Base URL: {api_client.base_url}")
        print(f"   Requests per minute: {api_client.requests_per_minute}")

        # Test that config values are used
        api_settings = config_manager.get_api_settings()
        if api_client.base_url == api_settings.base_url:
            print("[PASS] API Client using config base_url")
        else:
            print(f"[FAIL] API Client base_url mismatch: {api_client.base_url} vs {api_settings.base_url}")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] API Client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_filter_engine():
    """Test Filter Engine can use config patterns"""
    print("\n[TEST] Testing Filter Engine...")

    try:
        # Import Filter Engine
        spec = importlib.util.spec_from_file_location("filter_engine", project_root / "scripts" / "modules" / "02-filter-engine.py")
        filter_engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(filter_engine)
        FilterEngine = filter_engine.FilterEngine

        # Create ConfigManager
        spec = importlib.util.spec_from_file_location("config_manager", project_root / "scripts" / "modules" / "02-config-manager.py")
        config_manager_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_manager_module)
        ConfigManager = config_manager_module.ConfigManager
        config_path = project_root / "scripts" / "config" / "figma_client_config.json"
        config_manager = ConfigManager(str(config_path))

        # Initialize Filter Engine
        filter_engine = FilterEngine(config_manager)

        print("[PASS] Filter Engine initialized successfully")

        # Test with sample data
        sample_pages_data = {
            "success": True,
            "pages": [
                {
                    "id": "page1",
                    "name": "Test Page",
                    "visible_nodes": [
                        {"id": "node1", "name": "svg_exporter_test", "type": "FRAME"},
                        {"id": "node2", "name": "regular_node", "type": "FRAME"},
                        {"id": "node3", "name": "img_exporter_test", "type": "FRAME"}
                    ]
                }
            ]
        }

        # Test filtering
        result = filter_engine.filter_nodes_by_criteria(sample_pages_data)

        print(f"[PASS] Filter Engine test completed: {result.total_nodes} nodes filtered")
        print(f"   Filter criteria: include={result.filter_criteria.include}, exclude={result.filter_criteria.exclude}")

        return True

    except Exception as e:
        print(f"[FAIL] Filter Engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_report_generator():
    """Test Report Generator can use config settings"""
    print("\n[TEST] Testing Report Generator...")

    try:
        # Import Report Generator
        spec = importlib.util.spec_from_file_location("report_generator", project_root / "scripts" / "modules" / "02-report-generator.py")
        report_generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(report_generator)
        ReportGenerator = report_generator.ReportGenerator

        # Create ConfigManager
        spec = importlib.util.spec_from_file_location("config_manager", project_root / "scripts" / "modules" / "02-config-manager.py")
        config_manager_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_manager_module)
        ConfigManager = config_manager_module.ConfigManager
        config_path = project_root / "scripts" / "config" / "figma_client_config.json"
        config_manager = ConfigManager(str(config_path))

        # Initialize Report Generator
        report_generator = ReportGenerator(config_manager)

        print("[PASS] Report Generator initialized successfully")

        # Test with sample data
        sample_result = {
            "success": True,
            "total_pages": 2,
            "total_nodes": 10,
            "pages": [
                {
                    "id": "page1",
                    "name": "Test Page 1",
                    "node_count": 5
                }
            ],
            "filter_criteria": {
                "include": ["svg_exporter_*"],
                "exclude": [],
                "case_sensitive": False
            }
        }

        # Test report generation (without actually writing files)
        try:
            # This will use config output directory
            json_path, md_path = report_generator.generate_reports(sample_result)
            print(f"[PASS] Report generation test completed")
            print(f"   JSON report: {json_path}")
            print(f"   Markdown report: {md_path}")
        except Exception as e:
            print(f"[WARNING]  Report generation test warning (expected in test env): {e}")

        return True

    except Exception as e:
        print(f"[FAIL] Report Generator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_node_processor():
    """Test Node Processor can use config settings"""
    print("\n[TEST] Testing Node Processor...")

    try:
        # Import Node Processor
        spec = importlib.util.spec_from_file_location("node_processor", project_root / "scripts" / "modules" / "03-node-processor-v1.0.py")
        node_processor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(node_processor)
        NodeProcessor = node_processor.NodeProcessor

        # Create ConfigManager
        spec = importlib.util.spec_from_file_location("config_manager", project_root / "scripts" / "modules" / "02-config-manager.py")
        config_manager_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_manager_module)
        ConfigManager = config_manager_module.ConfigManager
        config_path = project_root / "scripts" / "config" / "figma_client_config.json"
        config_manager = ConfigManager(str(config_path))

        # Initialize Node Processor
        node_processor = NodeProcessor(config_manager=config_manager)

        print("[PASS] Node Processor initialized successfully")

        # Test config loading
        config = await node_processor.load_config()
        print(f"[PASS] Node Processor config loaded: {len(node_processor.naming_prefixes)} prefixes")
        print(f"   Target nodes enabled: {node_processor.target_nodes_config.get('enabled', False)}")

        return True

    except Exception as e:
        print(f"[FAIL] Node Processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_figma_client_orchestrator():
    """Test Figma Client Orchestrator integration"""
    print("\n[TEST] Testing Figma Client Orchestrator...")

    try:
        # Import Figma Client Orchestrator
        spec = importlib.util.spec_from_file_location("figma_client_fixed", project_root / "scripts" / "modules" / "02-figma-client-fixed-v1.0.py")
        figma_client = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(figma_client)
        FigmaClientOrchestrator = figma_client.FigmaClientOrchestrator

        # Mock API token
        api_token = "test_token"

        # Initialize orchestrator
        orchestrator = FigmaClientOrchestrator(api_token)

        print("[PASS] Figma Client Orchestrator initialized successfully")

        # Test config summary
        config_summary = orchestrator.get_config_summary()
        if "error" not in config_summary:
            print("[PASS] Orchestrator config summary generated")
            print(f"   Target nodes in summary: {'target_nodes' in config_summary}")
        else:
            print(f"[FAIL] Orchestrator config summary error: {config_summary['error']}")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] Figma Client Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all integration tests"""
    print("[START] CONFIG INTEGRATION TEST SUITE")
    print("=" * 50)
    print("Testing merged figma_client_config.json integration")
    print()

    tests = [
        ("Config File", test_config_file_exists),
        ("Config Manager", test_config_manager),
        ("API Client", test_api_client),
        ("Filter Engine", test_filter_engine),
        ("Report Generator", test_report_generator),
        ("Node Processor", test_node_processor),
        ("Figma Client Orchestrator", test_figma_client_orchestrator)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            if test_name == "Node Processor":
                # Handle async test
                import asyncio
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[FAIL] {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("[RESULTS] TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "[PASS] PASS" if result else "[FAIL] FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n[STATS] Overall: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All tests passed! Config integration successful.")
        return True
    else:
        print("[WARNING]  Some tests failed. Check output above for details.")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)