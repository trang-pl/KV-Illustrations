"""
API Models và Schemas cho MCP Figma Sync Server
API models and schemas for MCP Figma Sync Server
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class NodeStatus(str, Enum):
    """Trạng thái phát triển của node"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    READY = "ready"
    UNKNOWN = "unknown"


class ChangeStatus(str, Enum):
    """Trạng thái thay đổi của node"""
    NEW = "new"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    DELETED = "deleted"


class SyncStatus(str, Enum):
    """Trạng thái đồng bộ"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class NamingFilters(BaseModel):
    """Bộ lọc naming cho nodes"""
    include_patterns: List[str] = Field(default_factory=lambda: ["svg_export_*", "image_export_*", "icon_*"])
    exclude_patterns: List[str] = Field(default_factory=lambda: ["temp_*", "draft_*"])
    case_sensitive: bool = False


class SyncTriggerRequest(BaseModel):
    """Request để trigger đồng bộ"""
    file_key: str = Field(..., description="Figma file key")
    node_id: str = Field(..., description="Root node ID để export")
    output_dir: str = Field(..., description="Thư mục output")
    force_sync: bool = Field(False, description="Buộc đồng bộ tất cả nodes")
    commit_message: Optional[str] = Field(None, description="Thông điệp commit")
    naming_filters: Optional[NamingFilters] = Field(None, description="Bộ lọc naming")


class SyncTriggerResponse(BaseModel):
    """Response khi trigger đồng bộ"""
    sync_id: str = Field(..., description="ID của sync job")
    status: SyncStatus = Field(..., description="Trạng thái hiện tại")
    message: str = Field(..., description="Thông điệp")
    filters_applied: Dict[str, int] = Field(..., description="Số lượng filters đã áp dụng")


class ProgressInfo(BaseModel):
    """Thông tin tiến độ"""
    total_nodes: int = Field(..., description="Tổng số nodes")
    processed: int = Field(..., description="Số nodes đã xử lý")
    exported: int = Field(..., description="Số nodes đã export")
    failed: int = Field(..., description="Số nodes thất bại")


class ChangeStats(BaseModel):
    """Thống kê thay đổi"""
    new: int = Field(..., description="Số nodes mới")
    modified: int = Field(..., description="Số nodes đã sửa")
    unchanged: int = Field(..., description="Số nodes không đổi")
    deleted: int = Field(..., description="Số nodes đã xóa")


class DevReadyStats(BaseModel):
    """Thống kê dev-ready"""
    ready: int = Field(..., description="Số nodes ready")
    approved: int = Field(..., description="Số nodes approved")
    review: int = Field(..., description="Số nodes cần review")
    draft: int = Field(..., description="Số nodes draft")


class GitCommitInfo(BaseModel):
    """Thông tin git commit"""
    hash: str = Field(..., description="Commit hash")
    message: str = Field(..., description="Commit message")
    timestamp: str = Field(..., description="Thời gian commit")


class SyncStatusResponse(BaseModel):
    """Response trạng thái đồng bộ"""
    sync_id: str = Field(..., description="ID của sync job")
    status: SyncStatus = Field(..., description="Trạng thái hiện tại")
    progress: ProgressInfo = Field(..., description="Thông tin tiến độ")
    change_stats: ChangeStats = Field(..., description="Thống kê thay đổi")
    dev_ready_stats: DevReadyStats = Field(..., description="Thống kê dev-ready")
    git_commit: Optional[GitCommitInfo] = Field(None, description="Thông tin git commit")
    errors: List[str] = Field(default_factory=list, description="Danh sách lỗi")


class ConfigUpdateRequest(BaseModel):
    """Request cập nhật cấu hình"""
    figma: Optional[Dict] = Field(None, description="Cấu hình Figma")
    git: Optional[Dict] = Field(None, description="Cấu hình Git")
    sync: Optional[Dict] = Field(None, description="Cấu hình Sync")
    server: Optional[Dict] = Field(None, description="Cấu hình Server")


class ConfigResponse(BaseModel):
    """Response cấu hình hiện tại"""
    figma: Dict = Field(..., description="Cấu hình Figma")
    git: Dict = Field(..., description="Cấu hình Git")
    sync: Dict = Field(..., description="Cấu hình Sync")
    server: Dict = Field(..., description="Cấu hình Server")


class SyncHistoryItem(BaseModel):
    """Item trong lịch sử đồng bộ"""
    sync_id: str = Field(..., description="ID của sync job")
    file_key: str = Field(..., description="Figma file key")
    node_id: str = Field(..., description="Root node ID")
    status: SyncStatus = Field(..., description="Trạng thái cuối cùng")
    created_at: datetime = Field(..., description="Thời gian tạo")
    completed_at: Optional[datetime] = Field(None, description="Thời gian hoàn thành")
    exported_count: int = Field(..., description="Số nodes đã export")
    failed_count: int = Field(..., description="Số nodes thất bại")
    commit_hash: Optional[str] = Field(None, description="Git commit hash")


class SyncHistoryResponse(BaseModel):
    """Response lịch sử đồng bộ"""
    items: List[SyncHistoryItem] = Field(..., description="Danh sách sync jobs")
    total: int = Field(..., description="Tổng số items")
    page: int = Field(..., description="Trang hiện tại")
    page_size: int = Field(..., description="Kích thước trang")


class HealthResponse(BaseModel):
    """Response health check"""
    status: str = Field(..., description="Trạng thái hệ thống")
    timestamp: datetime = Field(default_factory=datetime.now, description="Thời gian check")
    version: str = Field(..., description="Phiên bản server")
    uptime: str = Field(..., description="Thời gian hoạt động")


class ErrorResponse(BaseModel):
    """Response lỗi"""
    error: str = Field(..., description="Thông điệp lỗi")
    code: str = Field(..., description="Mã lỗi")
    details: Optional[Dict] = Field(None, description="Chi tiết lỗi")