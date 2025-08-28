#!/usr/bin/env python3
"""
Integration Test Script
Kiểm tra tích hợp với logic từ script gốc
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root and server to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "server"))

from server.services.figma_sync import FigmaSyncService
from server.services.change_detector import ChangeDetector, NodeInfo, NodeStatus, ChangeStatus
from server.services.dev_ready_detector import DevReadyDetector
from config.settings import settings


async def test_change_detector():
    """Test ChangeDetector với dữ liệu mẫu"""
    print("[TEST] Testing ChangeDetector...")

    # Tạo cache file tạm
    cache_file = Path("./test_cache.json")

    # Khởi tạo detector
    detector = ChangeDetector(cache_file)

    # Dữ liệu mẫu
    sample_nodes = [
        {
            "id": "node1",
            "name": "icon-user",
            "type": "COMPONENT",
            "width": 24,
            "height": 24,
            "lastModified": "2025-08-28T00:00:00Z",
            "version": 1,
            "path": "root/icon-user",
            "depth": 1
        },
        {
            "id": "node2",
            "name": "icon-home",
            "type": "COMPONENT",
            "width": 24,
            "height": 24,
            "lastModified": "2025-08-28T00:00:00Z",
            "version": 1,
            "path": "root/icon-home",
            "depth": 1
        }
    ]

    # Phát hiện thay đổi
    nodes, change_stats = detector.detect_changes(sample_nodes, "test-version")

    print(f"[OK] Detected {len(nodes)} nodes")
    print(f"[STATS] Change stats: {change_stats}")

    # Dọn dẹp
    if cache_file.exists():
        cache_file.unlink()

    return True


async def test_dev_ready_detector():
    """Test DevReadyDetector với dữ liệu mẫu"""
    print("[TEST] Testing DevReadyDetector...")

    detector = DevReadyDetector()

    # Tạo node mẫu
    sample_node = NodeInfo(
        id="test-node",
        name="user-profile-icon",
        type="COMPONENT",
        width=24,
        height=24,
        last_modified="2025-08-28T00:00:00Z",
        version=1,
        path="root/user-profile-icon",
        depth=1,
        status=NodeStatus.UNKNOWN,
        change_status=ChangeStatus.NEW,
        dev_ready_score=0.0,
        issues=[]
    )

    # Danh gia readiness
    score, issues, status = detector.assess_readiness(sample_node)

    print("[OK] Dev-ready assessment:")
    print(f"   [SCORE] Score: {score:.2f}")
    print(f"   [STATUS] Status: {status.value}")
    print(f"   [ISSUES] Issues: {len(issues)}")

    return True


def test_naming_filters():
    """Kiểm tra bộ lọc đặt tên"""
    print("[TEST] Testing naming filters...")

    from server.services.change_detector import ChangeDetector

    # Tạo detector
    detector = ChangeDetector(Path("./dummy_cache.json"))

    # Dữ liệu mẫu
    nodes = [
        NodeInfo(
            id="1", name="svg_export_user", type="COMPONENT", width=24, height=24,
            last_modified="", version=1, path="root/svg_export_user", depth=1,
            status=NodeStatus.UNKNOWN, change_status=ChangeStatus.NEW,
            dev_ready_score=0.0, issues=[]
        ),
        NodeInfo(
            id="2", name="temp_draft", type="COMPONENT", width=24, height=24,
            last_modified="", version=1, path="root/temp_draft", depth=1,
            status=NodeStatus.UNKNOWN, change_status=ChangeStatus.NEW,
            dev_ready_score=0.0, issues=[]
        ),
        NodeInfo(
            id="3", name="icon_heart", type="COMPONENT", width=24, height=24,
            last_modified="", version=1, path="root/icon_heart", depth=1,
            status=NodeStatus.UNKNOWN, change_status=ChangeStatus.NEW,
            dev_ready_score=0.0, issues=[]
        )
    ]

    # Kiểm tra bộ lọc
    filters = {
        "include_patterns": ["svg_export_*", "icon_*"],
        "exclude_patterns": ["temp_*", "draft_*"],
        "case_sensitive": False
    }

    filtered_nodes = detector.apply_naming_filters(nodes, filters)

    print(f"[OK] Filtered {len(filtered_nodes)} from {len(nodes)} nodes")
    for node in filtered_nodes:
        print(f"   [FILE] {node.name}")

    return True


async def test_config_loading():
    """Kiểm tra tải cấu hình"""
    print("[TEST] Testing configuration loading...")

    from config.settings import settings

    print("[OK] Configuration loaded:")
    print(f"   [CONFIG] Figma batch size: {settings.figma.batch_size}")
    print(f"   [CONFIG] Delay between batches: {settings.figma.delay_between_batches}s")
    print(f"   [CONFIG] Server host: {settings.server.host}:{settings.server.port}")
    print(f"   [CONFIG] Log level: {settings.log_level}")

    return True


async def main():
    """Chạy tất cả tests"""
    print("[START] Running MCP Figma Sync Server Integration Tests")
    print("=" * 60)

    tests = [
        ("Configuration Loading", test_config_loading),
        ("Change Detector", test_change_detector),
        ("Dev Ready Detector", test_dev_ready_detector),
        ("Naming Filters", test_naming_filters),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n--- {test_name} ---")
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
            print(f"[PASS] {test_name}: PASSED")
        except Exception as e:
            results.append((test_name, False))
            print(f"[FAIL] {test_name}: FAILED - {e}")

    # Tổng kết
    print(f"\n[RESULTS] Test Results:")
    print("=" * 30)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS] PASS" if result else "[FAIL] FAIL"
        print(f"   {status} {test_name}")

    print(f"\n[SUMMARY] Overall: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All integration tests passed!")
        return 0
    else:
        print("[WARNING] Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())

    sys.exit(exit_code)