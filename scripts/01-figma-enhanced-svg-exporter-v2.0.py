#!/usr/bin/env python3
"""
Enhanced Figma SVG Export System
===============================
Production-ready SVG exporter with change detection, dev-ready status,
and optimized batch processing.

Features:
- Change detection based on lastModified timestamps
- Dev-ready status assessment
- Optimized batch processing (10 nodes/batch)
- Smart caching and incremental exports
- Comprehensive monitoring and reporting

Author: DS Tools
Version: 2.0.0
Date: 2025-08-27
"""

import os
import sys
import json
import requests
import asyncio
import aiohttp
from datetime import datetime, timezone
from pathlib import Path
import time
import hashlib
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from config.settings import settings

# Configuration
DEFAULT_CONFIG = {
    "batch_size": 10,  # Optimized from testing
    "delay_between_batches": 1.5,  # Optimized from testing
    "max_concurrent_requests": 5,
    "retry_delay": 60,
    "max_retries": 3,
    "cache_duration": 3600,  # 1 hour cache
    "dev_ready_threshold": 0.8,  # 80% score for dev-ready
}


class NodeStatus(Enum):
    """Node development status"""

    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    READY = "ready"
    UNKNOWN = "unknown"


class ChangeStatus(Enum):
    """Node change status"""

    NEW = "new"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    DELETED = "deleted"


@dataclass
class NodeInfo:
    """Complete node information"""

    id: str
    name: str
    type: str
    width: float
    height: float
    last_modified: Optional[str]
    version: int
    path: str
    depth: int
    status: NodeStatus
    change_status: ChangeStatus
    dev_ready_score: float
    issues: List[str]
    exported_at: Optional[str] = None
    svg_size: Optional[int] = None


class ChangeDetector:
    """Detects changes in Figma nodes"""

    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.last_export_data = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load previous export data from cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"📚 Loaded cache with {len(data.get('nodes', {}))} nodes")
                    return data
            except Exception as e:
                print(f"⚠️ Failed to load cache: {e}")
        return {"nodes": {}, "last_export": None, "file_version": None}

    def _save_cache(self, nodes: List[NodeInfo], file_version: str):
        """Save current export data to cache"""
        cache_data = {
            "nodes": {
                node.id: {
                    "name": node.name,
                    "last_modified": node.last_modified,
                    "version": node.version,
                    "exported_at": node.exported_at,
                    "dev_ready_score": node.dev_ready_score,
                    "status": node.status.value,
                    "svg_size": node.svg_size,
                }
                for node in nodes
            },
            "last_export": datetime.now().isoformat(),
            "file_version": file_version,
        }

        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Cache updated with {len(cache_data['nodes'])} nodes")
        except Exception as e:
            print(f"⚠️ Failed to save cache: {e}")

    def detect_changes(
        self, current_nodes: List[Dict], file_version: str
    ) -> Tuple[List[NodeInfo], Dict[str, int]]:
        """Detect changes and return updated node info"""
        changes_stats = {"new": 0, "modified": 0, "unchanged": 0, "deleted": 0}
        updated_nodes = []
        current_node_ids = set()

        for node_data in current_nodes:
            node_id = node_data["id"]
            current_node_ids.add(node_id)

            # Get cached data
            cached_node = self.last_export_data.get("nodes", {}).get(node_id, {})

            # Determine change status
            change_status = ChangeStatus.NEW
            if cached_node:
                current_modified = node_data.get("lastModified")
                cached_modified = cached_node.get("last_modified")
                current_version = node_data.get("version", 0)
                cached_version = cached_node.get("version", 0)

                if current_modified == cached_modified and current_version == cached_version:
                    change_status = ChangeStatus.UNCHANGED
                else:
                    change_status = ChangeStatus.MODIFIED

            # Create node info
            node_info = NodeInfo(
                id=node_id,
                name=node_data["name"],
                type=node_data["type"],
