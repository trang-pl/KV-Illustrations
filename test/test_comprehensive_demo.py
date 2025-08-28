#!/usr/bin/env python3
"""
Comprehensive Demo Script for Figma SVG Export
Demo cả Prefix Naming Mode và Node ID Mode với dữ liệu thực tế từ .env

Tính năng:
- Test prefix mode với multiple patterns
- Test node ID mode với fallback strategies
- So sánh performance và kết quả
- Detailed reporting và analytics
- Error handling và validation
"""

import asyncio
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

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


@dataclass
class TestResult:
    """Kết quả test cho một mode"""
    mode: str
    success: bool
    exported: int
    failed: int
    skipped: int
    dev_ready: int
    needs_review: int
    elapsed_time: float
    error: Optional[str] = None
    details: Optional[Dict] = None


@dataclass
class ComprehensiveConfig:
    """Cấu hình comprehensive cho cả hai modes"""

    # Environment variables
    figma_token: str
    file_key: str

    # Test configuration
    force_sync: bool = True
    batch_size: int = 10
    delay_between_batches: float = 1.0

    # Output directories
    base_output_dir: str = "./test/exports/comprehensive_demo"
    prefix_output_dir: str = ""
    node_id_output_dir: str = ""

    # Prefix mode patterns
    prefix_patterns: List[str] = None

    # Node ID mode targets
    node_id_targets: List[str] = None

    def __post_init__(self):
        """Initialize derived attributes"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.prefix_output_dir = f"{self.base_output_dir}/prefix_mode_{timestamp}"
        self.node_id_output_dir = f"{self.base_output_dir}/node_id_mode_{timestamp}"

        if self.prefix_patterns is None:
            self.prefix_patterns = [
                "svg_exporter_*",
                "icon_*",
                "component_*",
                "asset_*"
            ]

        if self.node_id_targets is None:
            self.node_id_targets = [
                "0:1",      # Root node
                "1:2",      # Common page node
                "2:3",      # Common frame node
            ]


class EnvironmentValidator:
    """Validate environment và dependencies"""

    @staticmethod
    def validate_environment() -> Tuple[bool, List[str]]:
        """Validate môi trường và trả về (is_valid, issues)"""
        issues = []

        # Check environment variables
        required_vars = ['FIGMA_API_TOKEN', 'FIGMA_FILE_KEY']
        for var in required_vars:
            if not os.environ.get(var):
                issues.append(f"Missing environment variable: {var}")

        # Check token format (basic validation)
        token = os.environ.get('FIGMA_API_TOKEN', '')
        if token and len(token) < 20:
            issues.append("FIGMA_API_TOKEN appears to be too short")

        # Check file key format (basic validation)
        file_key = os.environ.get('FIGMA_FILE_KEY', '')
        if file_key and not file_key.replace('-', '').replace('_', '').isalnum():
            issues.append("FIGMA_FILE_KEY contains invalid characters")

        # Check Python dependencies
        try:
            import aiohttp
            import dotenv
        except ImportError as e:
            issues.append(f"Missing Python dependency: {e}")

        return len(issues) == 0, issues

    @staticmethod
    def print_environment_info():
        """Print thông tin môi trường"""
        print("ENVIRONMENT INFO")
        print("=" * 50)
        print(f"Python: {sys.version}")
        print(f"Working Directory: {os.getcwd()}")
        print(f"Project Root: {project_root.absolute()}")

        # Environment variables (masked)
        token = os.environ.get('FIGMA_API_TOKEN', '')
        file_key = os.environ.get('FIGMA_FILE_KEY', '')

        print(f"FIGMA_API_TOKEN: {'SET' if token else 'MISSING'} ({len(token)} chars)")
        print(f"FIGMA_FILE_KEY: {'SET' if file_key else 'MISSING'} ({len(file_key)} chars)")

        if token:
            print(f"Token Preview: {token[:10]}...{token[-5:] if len(token) > 15 else token}")
        if file_key:
            print(f"File Key Preview: {file_key[:10]}...{file_key[-5:] if len(file_key) > 15 else file_key}")


class PrefixModeTester:
    """Test prefix naming mode với multiple patterns"""

    def __init__(self, service: FigmaSyncService, config: ComprehensiveConfig):
        self.service = service
        self.config = config
        self.results = {}

    async def test_single_pattern(self, pattern: str) -> TestResult:
        """Test một prefix pattern"""
        print(f"\n[TEST] Testing prefix pattern: {pattern}")
        print("-" * 50)

        start_time = time.time()

        try:
            # Create pattern-specific output directory
            pattern_name = pattern.replace('*', 'all').replace('_', '-')
            output_dir = f"{self.config.prefix_output_dir}/{pattern_name}"

            result = await self.service.process_sync(
                file_key=self.config.file_key,
                node_id="0:1",  # Root node
                output_dir=output_dir,
                force_sync=self.config.force_sync,
                naming_filters={
                    "include_patterns": [pattern],
                    "exclude_patterns": ["temp_*", "draft_*", "test_*"],
                    "case_sensitive": False
                }
            )

            elapsed = time.time() - start_time

            test_result = TestResult(
                mode=f"prefix_{pattern}",
                success="error" not in result,
                exported=result.get("exported", 0),
                failed=result.get("failed", 0),
                skipped=result.get("skipped", 0),
                dev_ready=result.get("dev_ready", 0),
                needs_review=result.get("needs_review", 0),
                elapsed_time=elapsed,
                error=result.get("error"),
                details=result
            )

            print(f"[RESULT] {pattern}: {test_result.exported} exported, {elapsed:.2f}s")

            return test_result

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"[ERROR] {pattern}: {str(e)}")

            return TestResult(
                mode=f"prefix_{pattern}",
                success=False,
                exported=0,
                failed=0,
                skipped=0,
                dev_ready=0,
                needs_review=0,
                elapsed_time=elapsed,
                error=str(e)
            )

    async def test_all_patterns(self) -> Dict[str, TestResult]:
        """Test tất cả prefix patterns"""
        print("\nPREFIX MODE TESTING")
        print("=" * 70)

        results = {}

        for pattern in self.config.prefix_patterns:
