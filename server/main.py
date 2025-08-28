"""
Main FastAPI Application
Ứng dụng FastAPI chính cho MCP Figma Sync Server
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any
import uvicorn

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from .api.models.schemas import (
    SyncTriggerRequest, SyncTriggerResponse, SyncStatusResponse,
    ConfigResponse, ConfigUpdateRequest, SyncHistoryResponse,
    HealthResponse, ErrorResponse, SyncStatus
)
from .services.figma_sync import FigmaSyncService
from .workers.background_worker import BackgroundWorker
from .utils.helpers import generate_sync_id, validate_file_key, validate_node_id


# Cấu hình logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Dịch vụ toàn cục
sync_service = FigmaSyncService()
background_worker = BackgroundWorker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời ứng dụng"""
    logger.info("🚀 Starting MCP Figma Sync Server")

    # Tác vụ khởi động
    await background_worker.start()

    yield

    # Tác vụ tắt máy
    await background_worker.stop()
    logger.info("🛑 MCP Figma Sync Server stopped")


# Tạo ứng dụng FastAPI
app = FastAPI(
    title="MCP Figma Sync Server",
    description="Server đồng bộ SVG từ Figma với MCP support",
    version="1.0.0",
    lifespan=lifespan
)

# Thêm middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=str(datetime.now() - background_worker.start_time)
    )


@app.post("/api/v1/sync/trigger", response_model=SyncTriggerResponse)
async def trigger_sync(
    request: SyncTriggerRequest,
    background_tasks: BackgroundTasks
):
    """Trigger đồng bộ từ Figma"""
    try:
        # Xác thực đầu vào
        if not validate_file_key(request.file_key):
            raise HTTPException(status_code=400, detail="Invalid Figma file key")

        if not validate_node_id(request.node_id):
            raise HTTPException(status_code=400, detail="Invalid node ID")

        # Tạo ID đồng bộ
        sync_id = generate_sync_id()

        # Đưa tác vụ đồng bộ vào hàng đợi
        background_tasks.add_task(
            background_worker.process_sync_job,
            sync_id=sync_id,
            file_key=request.file_key,
            node_id=request.node_id,
            output_dir=request.output_dir,
            force_sync=request.force_sync,
            commit_message=request.commit_message,
            naming_filters=request.naming_filters.dict() if request.naming_filters else None
        )

        # Đếm bộ lọc đã áp dụng
        filters_applied = {"include_count": 0, "exclude_count": 0}
        if request.naming_filters:
            filters_applied["include_count"] = len(request.naming_filters.include_patterns)
            filters_applied["exclude_count"] = len(request.naming_filters.exclude_patterns)

        logger.info(f"📝 Sync job queued: {sync_id} for file {request.file_key}")

        return SyncTriggerResponse(
            sync_id=sync_id,
            status=SyncStatus.QUEUED,
            message="Sync job queued successfully",
            filters_applied=filters_applied
        )

    except Exception as e:
        logger.error(f"❌ Error triggering sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sync/{sync_id}/status", response_model=SyncStatusResponse)
async def get_sync_status(sync_id: str):
    """Lấy trạng thái đồng bộ"""
    try:
        status_data = background_worker.get_sync_status(sync_id)
        if not status_data:
            raise HTTPException(status_code=404, detail="Sync job not found")

        return SyncStatusResponse(**status_data)

    except Exception as e:
        logger.error(f"❌ Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/config", response_model=ConfigResponse)
async def get_config():
    """Lấy cấu hình hiện tại"""
    try:
        return ConfigResponse(
            figma=settings.figma.dict(),
            git=settings.git.dict(),
            sync=settings.sync.dict(),
            server=settings.server.dict()
        )
    except Exception as e:
        logger.error(f"❌ Error getting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/config")
async def update_config(request: ConfigUpdateRequest):
    """Cập nhật cấu hình"""
    try:
        # Điều này sẽ cập nhật cấu hình
        # Hiện tại chỉ trả về thành công
        logger.info("📝 Config update requested")
        return {"message": "Configuration update not implemented yet"}

    except Exception as e:
        logger.error(f"❌ Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sync/history", response_model=SyncHistoryResponse)
async def get_sync_history(page: int = 1, page_size: int = 10):
    """Lấy lịch sử đồng bộ"""
    try:
        # Điều này sẽ trả về lịch sử đồng bộ từ database/storage
        # Hiện tại trả về phản hồi trống
        return SyncHistoryResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"❌ Error getting sync history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"💥 Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            code="INTERNAL_ERROR",
            details={"message": str(exc)}
        ).dict()
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=True,
        log_level=settings.log_level.lower()
    )