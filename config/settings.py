"""
Cấu hình hệ thống MCP Figma Sync Server
Configuration management for MCP Figma Sync Server
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Add project root to sys.path to enable imports from config
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class FigmaConfig(BaseSettings):
    """Cấu hình Figma API"""

    api_token: Optional[str] = Field(None, env="FIGMA_API_TOKEN")
    batch_size: int = Field(10, description="Số node xử lý mỗi batch")
    delay_between_batches: float = Field(1.5, description="Độ trễ giữa các batch (giây)")
    max_concurrent_requests: int = Field(5, description="Số request đồng thời tối đa")
    retry_delay: int = Field(60, description="Độ trễ retry khi rate limited")
    max_retries: int = Field(3, description="Số lần retry tối đa")


class GitConfig(BaseSettings):
    """Cấu hình Git integration"""

    repo_path: str = Field("./repo", description="Đường dẫn đến git repository")
    remote_name: str = Field("origin", description="Tên remote git")
    branch: str = Field("main", description="Branch mặc định")
    auto_commit: bool = Field(True, description="Tự động commit")
    auto_push: bool = Field(True, description="Tự động push")


class SyncConfig(BaseSettings):
    """Cấu hình đồng bộ"""

    cache_duration: int = Field(3600, description="Thời gian cache (giây)")
    dev_ready_threshold: float = Field(0.8, description="Ngưỡng dev-ready")
    force_sync_allowed: bool = Field(True, description="Cho phép force sync")
    default_naming_filters: Dict = Field({
        "include_patterns": ["svg_export_*", "image_export_*", "icon_*"],
        "exclude_patterns": ["temp_*", "draft_*"],
        "case_sensitive": False
    }, description="Bộ lọc naming mặc định")


class ServerConfig(BaseSettings):
    """Cấu hình server"""

    host: str = Field("localhost", description="Host server")
    port: int = Field(8001, description="Port server")
    cors_origins: List[str] = Field(["*"], description="CORS origins")


class Settings(BaseSettings):
    """Cấu hình tổng thể hệ thống"""

    # Database
    database_url: str = Field("sqlite:///./figma_sync.db", env="DATABASE_URL")

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # Sub-configs
    figma: FigmaConfig = FigmaConfig()
    git: GitConfig = GitConfig()
    sync: SyncConfig = SyncConfig()
    server: ServerConfig = ServerConfig()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )


# Global settings instance
settings = Settings()

def reload_settings():
    """Reload settings after loading environment variables"""
    import dotenv
    dotenv.load_dotenv()
    global settings
    settings = Settings()
    return settings


def load_config_from_file(config_path: Optional[Path] = None) -> Settings:
    """Load configuration from JSON file"""
    if config_path and config_path.exists():
        import json
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # Update settings with file data
        for key, value in config_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

    return settings


def save_config_to_file(config_path: Path, config: Settings):
    """Save configuration to JSON file"""
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config_dict = {
        "figma": config.figma.dict(),
        "git": config.git.dict(),
        "sync": config.sync.dict(),
        "server": config.server.dict(),
        "database_url": config.database_url,
        "log_level": config.log_level
    }

    with open(config_path, "w", encoding="utf-8") as f:
        import json
        json.dump(config_dict, f, indent=2, ensure_ascii=False)


# Load config from config/config.json if exists
config_file = Path("./config/config.json")
if config_file.exists():
    settings = load_config_from_file(config_file)