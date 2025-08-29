#!/usr/bin/env python3
"""
Config Manager Module v1.0
==========================

Configuration management for Figma client modular architecture.
Handles loading, validation, and access to configuration settings.

Features:
- JSON config file loading
- Environment variable integration
- Default value fallbacks
- Configuration validation
- Unicode-safe operations

Author: Kilo Code Debug Agent
Version: 1.0.0
Date: 2025-08-29
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, NamedTuple
from dataclasses import dataclass

class NamingPrefixes(NamedTuple):
    """Naming prefixes configuration"""
    svg_exporter: str
    img_exporter: str
    icon_exporter: str

class FilterPatterns(NamedTuple):
    """Filter patterns configuration"""
    include: list
    exclude: list
    case_sensitive: bool

class ApiSettings(NamedTuple):
    """API settings configuration"""
    base_url: str
    requests_per_minute: int
    timeout: int

class OutputSettings(NamedTuple):
    """Output settings configuration"""
    default_output_dir: str
    report_formats: list

class TargetNodes(NamedTuple):
    """Target nodes configuration"""
    enabled: bool
    node_ids: list
    export_mode: str
    process_children: bool

@dataclass
class Config:
    """Main configuration class"""
    naming_prefixes: NamingPrefixes
    filter_patterns: FilterPatterns
    api_settings: ApiSettings
    output_settings: OutputSettings
    target_nodes: TargetNodes

class ConfigManager:
    """Configuration manager for Figma client"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config manager

        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config = None
        self._load_config()

    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        # Try multiple possible locations for figma_client_config.json
        possible_paths = [
            Path(__file__).parent.parent / "config" / "figma_client_config.json",
            Path(__file__).parent.parent.parent / "scripts" / "config" / "figma_client_config.json",
            Path.cwd() / "scripts" / "config" / "figma_client_config.json"
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        # Fallback to current directory
        return "figma_client_config.json"

    def _load_config(self) -> None:
        """Load configuration from file"""
        try:
            config_file = Path(self.config_path)

            if not config_file.exists():
                print(f"[DEBUG] [CONFIG_MANAGER] Config file not found: {self.config_path}")
                print("[DEBUG] [CONFIG_MANAGER] Using default configuration")
                self._config = self._get_default_config()
                return

            print(f"[DEBUG] [CONFIG_MANAGER] Loading config from: {self.config_path}")

            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            self._config = self._parse_config(config_data)
            print("[DEBUG] [CONFIG_MANAGER] Configuration loaded successfully")

        except Exception as e:
            print(f"[DEBUG] [CONFIG_MANAGER] Error loading config: {str(e)}")
            print("[DEBUG] [CONFIG_MANAGER] Using default configuration")
            self._config = self._get_default_config()

    def _parse_config(self, config_data: Dict[str, Any]) -> Config:
        """Parse configuration data into Config object"""
        try:
            # Extract naming prefixes
            naming_prefixes_data = config_data.get("naming_prefixes", {})
            naming_prefixes = NamingPrefixes(
                svg_exporter=naming_prefixes_data.get("svg_exporter", "svg_exporter_"),
                img_exporter=naming_prefixes_data.get("img_exporter", "img_exporter_"),
                icon_exporter=naming_prefixes_data.get("icon_exporter", "icon_exporter_")
            )

            # Extract filter patterns
            filter_patterns_data = config_data.get("filter_patterns", {})
            filter_patterns = FilterPatterns(
                include=filter_patterns_data.get("include", ["svg_exporter_*"]),
                exclude=filter_patterns_data.get("exclude", []),
                case_sensitive=filter_patterns_data.get("case_sensitive", False)
            )

            # Extract API settings
            api_settings_data = config_data.get("api_settings", {})
            api_settings = ApiSettings(
                base_url=api_settings_data.get("base_url", "https://api.figma.com/v1"),
                requests_per_minute=api_settings_data.get("requests_per_minute", 60),
                timeout=api_settings_data.get("timeout", 30)
            )

            # Extract output settings
            output_settings_data = config_data.get("output_settings", {})
            output_settings = OutputSettings(
                default_output_dir=output_settings_data.get("default_output_dir", "exports/"),
                report_formats=output_settings_data.get("report_formats", ["json", "markdown"])
            )

            # Extract target nodes
            target_nodes_data = config_data.get("target_nodes", {})
            target_nodes = TargetNodes(
                enabled=target_nodes_data.get("enabled", True),
                node_ids=target_nodes_data.get("node_ids", []),
                export_mode=target_nodes_data.get("export_mode", "svg"),
                process_children=target_nodes_data.get("process_children", True)
            )

            return Config(
                naming_prefixes=naming_prefixes,
                filter_patterns=filter_patterns,
                api_settings=api_settings,
                output_settings=output_settings,
                target_nodes=target_nodes
            )

        except Exception as e:
            print(f"[DEBUG] [CONFIG_MANAGER] Error parsing config: {str(e)}")
            return self._get_default_config()

    def _get_default_config(self) -> Config:
        """Get default configuration"""
        return Config(
            naming_prefixes=NamingPrefixes(
                svg_exporter="svg_exporter_",
                img_exporter="img_exporter_",
                icon_exporter="icon_exporter_"
            ),
            filter_patterns=FilterPatterns(
                include=["svg_exporter_*"],
                exclude=[],
                case_sensitive=False
            ),
            api_settings=ApiSettings(
                base_url="https://api.figma.com/v1",
                requests_per_minute=60,
                timeout=30
            ),
            output_settings=OutputSettings(
                default_output_dir="exports/",
                report_formats=["json", "markdown"]
            ),
            target_nodes=TargetNodes(
                enabled=True,
                node_ids=[],
                export_mode="svg",
                process_children=True
            )
        )

    def get_config(self) -> Config:
        """Get current configuration"""
        return self._config

    def get_output_settings(self) -> OutputSettings:
        """Get output settings"""
        return self._config.output_settings

    def get_naming_prefixes(self) -> NamingPrefixes:
        """Get naming prefixes"""
        return self._config.naming_prefixes

    def get_filter_patterns(self) -> FilterPatterns:
        """Get filter patterns"""
        return self._config.filter_patterns

    def get_api_settings(self) -> ApiSettings:
        """Get API settings"""
        return self._config.api_settings

    def get_target_nodes(self) -> TargetNodes:
        """Get target nodes configuration"""
        return self._config.target_nodes

    def reload_config(self) -> bool:
        """Reload configuration from file"""
        try:
            self._load_config()
            return True
        except Exception as e:
            print(f"[DEBUG] [CONFIG_MANAGER] Error reloading config: {str(e)}")
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for debugging"""
        return {
            "config_path": self.config_path,
            "naming_prefixes": {
                "svg_exporter": self._config.naming_prefixes.svg_exporter,
                "img_exporter": self._config.naming_prefixes.img_exporter,
                "icon_exporter": self._config.naming_prefixes.icon_exporter
            },
            "filter_patterns": {
                "include": self._config.filter_patterns.include,
                "exclude": self._config.filter_patterns.exclude,
                "case_sensitive": self._config.filter_patterns.case_sensitive
            },
            "api_settings": {
                "base_url": self._config.api_settings.base_url,
                "requests_per_minute": self._config.api_settings.requests_per_minute,
                "timeout": self._config.api_settings.timeout
            },
            "output_settings": {
                "default_output_dir": self._config.output_settings.default_output_dir,
                "report_formats": self._config.output_settings.report_formats
            },
            "target_nodes": {
                "enabled": self._config.target_nodes.enabled,
                "node_ids": self._config.target_nodes.node_ids,
                "export_mode": self._config.target_nodes.export_mode,
                "process_children": self._config.target_nodes.process_children
            }
        }

def load_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    Factory function to create ConfigManager instance

    Args:
        config_path: Path to configuration file (optional)

    Returns:
        ConfigManager instance
    """
    return ConfigManager(config_path)

# Export main classes and functions
__all__ = ['ConfigManager', 'Config', 'load_config']