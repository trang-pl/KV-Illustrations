"""
Change Detector Service
Phát hiện thay đổi trong Figma nodes
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

from config.settings import settings


class NodeStatus(Enum):
    """Trạng thái phát triển của node"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    READY = "ready"
    UNKNOWN = "unknown"


class ChangeStatus(Enum):
    """Trạng thái thay đổi của node"""
    NEW = "new"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    DELETED = "deleted"


@dataclass
class NodeInfo:
    """Thông tin đầy đủ về node"""
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
    """Phát hiện thay đổi trong Figma nodes"""

    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.last_export_data = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Tải dữ liệu export trước từ cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"[CACHE] Da tai cache voi {len(data.get('nodes', {}))} nodes")
                    return data
            except Exception as e:
                print(f"[WARNING] Khong the tai cache: {e}")
        return {"nodes": {}, "last_export": None, "file_version": None}

    def _save_cache(self, nodes: List[NodeInfo], file_version: str):
        """Lưu dữ liệu export hiện tại vào cache"""
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
            print(f"[CACHE] Cache da cap nhat voi {len(cache_data['nodes'])} nodes")
        except Exception as e:
            print(f"[WARNING] Khong the luu cache: {e}")

    def detect_changes(
        self, current_nodes: List[Dict], file_version: str
    ) -> Tuple[List[NodeInfo], Dict[str, int]]:
        """Phát hiện thay đổi và trả về thông tin node đã cập nhật"""
        changes_stats = {"new": 0, "modified": 0, "unchanged": 0, "deleted": 0}
        updated_nodes = []
        current_node_ids = set()

        for node_data in current_nodes:
            node_id = node_data["id"]
            current_node_ids.add(node_id)

            # Lấy dữ liệu cached
            cached_node = self.last_export_data.get("nodes", {}).get(node_id, {})

            # Xác định trạng thái thay đổi
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

            # Tạo thông tin node
            node_info = NodeInfo(
                id=node_id,
                name=node_data["name"],
                type=node_data["type"],
                width=node_data.get("width", 0),
                height=node_data.get("height", 0),
                last_modified=node_data.get("lastModified"),
                version=node_data.get("version", 0),
                path=node_data["path"],
                depth=node_data["depth"],
                status=NodeStatus.UNKNOWN,  # Sẽ được đánh giá sau
                change_status=change_status,
                dev_ready_score=0.0,  # Sẽ được đánh giá sau
                issues=[],
            )

            updated_nodes.append(node_info)
            changes_stats[change_status.value] += 1

        # Phát hiện nodes đã xóa
        cached_node_ids = set(self.last_export_data.get("nodes", {}).keys())
        deleted_nodes = cached_node_ids - current_node_ids
        changes_stats["deleted"] = len(deleted_nodes)

        return updated_nodes, changes_stats

    def apply_naming_filters(
        self, nodes: List[NodeInfo], filters: Dict
    ) -> List[NodeInfo]:
        """Áp dụng bộ lọc naming cho nodes"""
        if not filters:
            return nodes

        include_patterns = filters.get("include_patterns", [])
        exclude_patterns = filters.get("exclude_patterns", [])
        case_sensitive = filters.get("case_sensitive", False)

        filtered_nodes = []

        for node in nodes:
            # Áp dụng include filter
            if include_patterns and not self._matches_pattern(
                node.name, include_patterns, case_sensitive
            ):
                continue

            # Áp dụng exclude filter
            if exclude_patterns and self._matches_pattern(
                node.name, exclude_patterns, case_sensitive
            ):
                continue

            filtered_nodes.append(node)

        return filtered_nodes

    def _matches_pattern(
        self, name: str, patterns: List[str], case_sensitive: bool = False
    ) -> bool:
        """Kiểm tra tên có khớp với pattern không"""
        flags = 0 if case_sensitive else re.IGNORECASE
        for pattern in patterns:
            # Chuyển wildcard thành regex
            regex_pattern = pattern.replace('*', '.*').replace('?', '.')
            try:
                if re.match(regex_pattern, name, flags):
                    return True
            except re.error:
                continue
        return False