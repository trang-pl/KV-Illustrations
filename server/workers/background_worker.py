"""
Background Worker
Worker xử lý các tác vụ đồng bộ bất đồng bộ
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from ..services.figma_sync import FigmaSyncService
from config.settings import settings
from ..utils.helpers import format_datetime


logger = logging.getLogger(__name__)


class BackgroundWorker:
    """Worker xử lý tác vụ đồng bộ bất đồng bộ"""

    def __init__(self):
        self.sync_service = FigmaSyncService()
        self.running_jobs: Dict[str, Dict[str, Any]] = {}
        self.completed_jobs: Dict[str, Dict[str, Any]] = {}
        self.start_time = datetime.now()
        self._running = False

    async def start(self):
        """Khởi động background worker"""
        self._running = True
        logger.info("🚀 Background worker started")

    async def stop(self):
        """Dừng background worker"""
        self._running = False
        logger.info("🛑 Background worker stopped")

    async def process_sync_job(
        self,
        sync_id: str,
        file_key: str,
        node_id: str,
        output_dir: str,
        force_sync: bool = False,
        commit_message: Optional[str] = None,
        naming_filters: Optional[Dict] = None
    ):
        """Xử lý sync job bất đồng bộ"""
        try:
            # Initialize job status
            self.running_jobs[sync_id] = {
                "sync_id": sync_id,
                "status": "running",
                "file_key": file_key,
                "node_id": node_id,
                "output_dir": output_dir,
                "force_sync": force_sync,
                "created_at": format_datetime(datetime.now()),
                "progress": {
                    "total_nodes": 0,
                    "processed": 0,
                    "exported": 0,
                    "failed": 0
                },
                "change_stats": {
                    "new": 0,
                    "modified": 0,
                    "unchanged": 0,
                    "deleted": 0
                },
                "dev_ready_stats": {
                    "ready": 0,
                    "approved": 0,
                    "review": 0,
                    "draft": 0
                },
                "errors": []
            }

            logger.info(f"🎯 Starting sync job: {sync_id}")

            # Process the sync
            result = await self.sync_service.process_sync(
                file_key=file_key,
                node_id=node_id,
                output_dir=output_dir,
                force_sync=force_sync,
                naming_filters=naming_filters
            )

            # Update job status
            self.running_jobs[sync_id].update({
                "status": "completed",
                "completed_at": format_datetime(datetime.now()),
                "progress": {
                    "total_nodes": result.get("total_nodes", 0),
                    "processed": result.get("processed", 0),
                    "exported": result.get("exported", 0),
                    "failed": result.get("failed", 0)
                },
                "change_stats": result.get("change_stats", {}),
                "dev_ready_stats": result.get("status_counts", {}),
                "export_stats": {
                    "exported": result.get("exported", 0),
                    "failed": result.get("failed", 0),
                    "skipped": result.get("skipped", 0),
                    "dev_ready": result.get("dev_ready", 0),
                    "needs_review": result.get("needs_review", 0)
                }
            })

            # Move to completed jobs
            self.completed_jobs[sync_id] = self.running_jobs.pop(sync_id)

            logger.info(f"✅ Sync job completed: {sync_id}")

        except Exception as e:
            logger.error(f"❌ Sync job failed: {sync_id} - {e}")

            # Update job status with error
            if sync_id in self.running_jobs:
                self.running_jobs[sync_id].update({
                    "status": "failed",
                    "completed_at": format_datetime(datetime.now()),
                    "errors": [str(e)]
                })
                self.completed_jobs[sync_id] = self.running_jobs.pop(sync_id)

    def get_sync_status(self, sync_id: str) -> Optional[Dict[str, Any]]:
        """Lấy trạng thái sync job"""
        if sync_id in self.running_jobs:
            return self.running_jobs[sync_id]
        elif sync_id in self.completed_jobs:
            return self.completed_jobs[sync_id]
        return None

    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Lấy tất cả jobs"""
        all_jobs = {}
        all_jobs.update(self.running_jobs)
        all_jobs.update(self.completed_jobs)
        return all_jobs

    def get_running_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Lấy jobs đang chạy"""
        return self.running_jobs.copy()

    def get_completed_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Lấy jobs đã hoàn thành"""
        return self.completed_jobs.copy()

    def cancel_job(self, sync_id: str) -> bool:
        """Hủy job (chưa implement)"""
        # For now, just mark as cancelled if running
        if sync_id in self.running_jobs:
            self.running_jobs[sync_id]["status"] = "cancelled"
            self.running_jobs[sync_id]["completed_at"] = format_datetime(datetime.now())
            self.completed_jobs[sync_id] = self.running_jobs.pop(sync_id)
            return True
        return False

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Dọn dẹp jobs cũ"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

        to_remove = []
        for sync_id, job in self.completed_jobs.items():
            if job.get("completed_at"):
                # This is a simplified check - in production you'd parse the datetime properly
                to_remove.append(sync_id)

        for sync_id in to_remove:
            del self.completed_jobs[sync_id]

        logger.info(f"🧹 Cleaned up {len(to_remove)} old jobs")

    def get_stats(self) -> Dict[str, Any]:
        """Lấy thống kê worker"""
        return {
            "running_jobs": len(self.running_jobs),
            "completed_jobs": len(self.completed_jobs),
            "total_jobs": len(self.running_jobs) + len(self.completed_jobs),
            "uptime": str(datetime.now() - self.start_time)
        }