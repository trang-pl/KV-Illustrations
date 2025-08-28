"""
Helper functions
Các hàm tiện ích cho MCP Figma Sync Server
"""

import re
import uuid
from datetime import datetime
from typing import Optional


def generate_sync_id() -> str:
    """Tạo ID duy nhất cho sync job"""
    return f"sync_{uuid.uuid4().hex[:16]}"


def validate_file_key(file_key: str) -> bool:
    """Xác thực khóa file Figma"""
    # Figma file keys are typically alphanumeric with possible hyphens
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, file_key)) and len(file_key) > 10


def validate_node_id(node_id: str) -> bool:
    """Xác thực ID node Figma"""
    # Node IDs typically contain colons and numbers
    pattern = r'^[0-9:]+$'
    return bool(re.match(pattern, node_id)) and len(node_id) > 5


def sanitize_filename(name: str) -> str:
    """Làm sạch tên file"""
    # Loại bỏ ký tự không hợp lệ
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")

    # Chuyển về lowercase và thay thế khoảng trắng
    name = name.lower().replace(" ", "-")

    # Loại bỏ dấu gạch ngang liên tiếp
    name = re.sub(r"[-_]+", "-", name)

    # Loại bỏ đầu cuối
    name = name.strip("-_")

    # Giới hạn độ dài
    if len(name) > 100:
        name = name[:100].rstrip("-_")

    return name or "unnamed"


def format_datetime(dt: datetime) -> str:
    """Format datetime thành string"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def calculate_percentage(part: int, total: int) -> float:
    """Tính phần trăm"""
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Cắt ngắn text nếu quá dài"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def safe_get(data: dict, key: str, default=None):
    """Lấy giá trị từ dict an toàn"""
    try:
        return data.get(key, default)
    except (AttributeError, TypeError):
        return default


def merge_dicts(base: dict, update: dict) -> dict:
    """Merge hai dictionaries"""
    result = base.copy()
    result.update(update)
    return result


def validate_config(config: dict) -> bool:
    """Validate cấu hình cơ bản"""
    required_keys = ["figma", "git", "sync", "server"]
    for key in required_keys:
        if key not in config:
            return False

    # Validate Figma config
    figma_config = config.get("figma", {})
    if not figma_config.get("api_token"):
        return False

    return True