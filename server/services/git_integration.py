"""
Git Integration Service
Dịch vụ tích hợp Git để commit và push thay đổi
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

try:
    import git
    from git import Repo, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    git = None
    Repo = None
    GitCommandError = None


from config.settings import settings
from ..utils.helpers import format_datetime


logger = logging.getLogger(__name__)


class GitIntegrationService:
    """Dịch vụ tích hợp Git"""

    def __init__(self):
        if not GIT_AVAILABLE:
            logger.warning("⚠️ GitPython not available. Git integration disabled.")
            self.enabled = False
        else:
            self.enabled = settings.git.auto_commit or settings.git.auto_push
            self.repo_path = Path(settings.git.repo_path)
            self.remote_name = settings.git.remote_name
            self.branch = settings.git.branch

    def is_enabled(self) -> bool:
        """Kiểm tra git integration có được bật không"""
        return self.enabled and GIT_AVAILABLE

    def is_git_repo(self) -> bool:
        """Kiểm tra thư mục có phải git repo không"""
        if not self.enabled:
            return False

        try:
            Repo(self.repo_path)
            return True
        except Exception:
            return False

    def init_repo(self) -> bool:
        """Khởi tạo git repo nếu chưa có"""
        if not self.enabled:
            return False

        try:
            if not self.repo_path.exists():
                self.repo_path.mkdir(parents=True, exist_ok=True)

            if not self.is_git_repo():
                Repo.init(self.repo_path)
                logger.info(f"📝 Initialized git repo at {self.repo_path}")

            return True
        except Exception as e:
            logger.error(f"❌ Failed to init git repo: {e}")
            return False

    def add_remote(self, remote_url: str) -> bool:
        """Thêm remote origin"""
        if not self.enabled:
            return False

        try:
            repo = Repo(self.repo_path)
            if self.remote_name not in repo.remotes:
                repo.create_remote(self.remote_name, remote_url)
                logger.info(f"🔗 Added remote {self.remote_name}: {remote_url}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add remote: {e}")
            return False

    def add_files(self, file_paths: list) -> bool:
        """Thêm files vào staging area"""
        if not self.enabled:
            return False

        try:
            repo = Repo(self.repo_path)
            repo.index.add(file_paths)
            logger.info(f"📁 Added {len(file_paths)} files to staging")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add files: {e}")
            return False

    def commit_changes(self, message: str, author_name: str = "MCP Figma Sync", author_email: str = "mcp-sync@localhost") -> Optional[str]:
        """Commit các thay đổi"""
        if not self.enabled:
            return None

        try:
            repo = Repo(self.repo_path)

            # Kiểm tra có thay đổi không
            if not repo.index.diff("HEAD", cached=True) and not repo.untracked_files:
                logger.info("📝 No changes to commit")
                return None

            # Tạo commit
            commit = repo.index.commit(
                message,
                author=git.Actor(author_name, author_email),
                committer=git.Actor(author_name, author_email)
            )

            logger.info(f"✅ Committed changes: {commit.hexsha[:8]}")
            return commit.hexsha

        except Exception as e:
            logger.error(f"❌ Failed to commit: {e}")
            return None

    def push_changes(self, remote_name: Optional[str] = None, branch: Optional[str] = None) -> bool:
        """Push thay đổi lên remote"""
        if not self.enabled:
            return False

        remote_name = remote_name or self.remote_name
        branch = branch or self.branch

        try:
            repo = Repo(self.repo_path)
            remote = repo.remote(remote_name)
            remote.push(branch)
            logger.info(f"🚀 Pushed to {remote_name}/{branch}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to push: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Lấy trạng thái git repo"""
        if not self.enabled:
            return {"enabled": False}

        try:
            repo = Repo(self.repo_path)

            status = {
                "enabled": True,
                "is_dirty": repo.is_dirty(),
                "untracked_files": len(repo.untracked_files),
                "staged_changes": len(repo.index.diff("HEAD", cached=True)),
                "ahead_behind": {},
                "current_branch": repo.active_branch.name if repo.active_branch else None
            }

            # Kiểm tra ahead/behind so với remote
            try:
                remote = repo.remote(self.remote_name)
                ahead, behind = repo.iter_commits(f"{self.remote_name}/{self.branch}..HEAD"), repo.iter_commits(f"HEAD..{self.remote_name}/{self.branch}")
                status["ahead_behind"] = {
                    "ahead": len(list(ahead)),
                    "behind": len(list(behind))
                }
            except Exception:
                pass

            return status

        except Exception as e:
            logger.error(f"❌ Failed to get git status: {e}")
            return {"enabled": False, "error": str(e)}

    def create_commit_message(self, change_stats: Dict[str, int], dev_ready_stats: Dict[str, int]) -> str:
        """Tạo commit message từ thống kê thay đổi"""
        total_changes = sum(change_stats.values())
        dev_ready_count = dev_ready_stats.get("ready", 0) + dev_ready_stats.get("approved", 0)

        message_lines = [
            "🔄 Sync Figma assets",
            f"",
            f"📊 Changes: +{change_stats.get('new', 0)} new, ~{change_stats.get('modified', 0)} modified, -{change_stats.get('deleted', 0)} deleted",
            f"🎯 Dev-ready: {dev_ready_count} assets ready for development",
            f"⏱️  Synced at {format_datetime(datetime.now())}"
        ]

        return "\n".join(message_lines)

    def sync_and_commit(
        self,
        file_paths: list,
        change_stats: Dict[str, int],
        dev_ready_stats: Dict[str, int],
        commit_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Đồng bộ và commit thay đổi"""
        if not self.enabled:
            return {"success": False, "error": "Git integration disabled"}

        result = {
            "success": False,
            "commit_hash": None,
            "pushed": False,
            "error": None
        }

        try:
            # Khởi tạo repo nếu cần
            if not self.init_repo():
                result["error"] = "Failed to initialize git repo"
                return result

            # Thêm files
            if not self.add_files(file_paths):
                result["error"] = "Failed to add files"
                return result

            # Tạo commit message
            if not commit_message:
                commit_message = self.create_commit_message(change_stats, dev_ready_stats)

            # Commit
            commit_hash = self.commit_changes(commit_message)
            if not commit_hash:
                result["error"] = "No changes to commit or commit failed"
                return result

            result["commit_hash"] = commit_hash

            # Push nếu được bật
            if settings.git.auto_push:
                if self.push_changes():
                    result["pushed"] = True
                else:
                    result["error"] = "Commit successful but push failed"

            result["success"] = True

        except Exception as e:
            logger.error(f"❌ Git sync failed: {e}")
            result["error"] = str(e)

        return result