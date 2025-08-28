# Máy chủ đồng bộ MCP Figma

Máy chủ đồng bộ SVG từ Figma với hỗ trợ MCP (Model Context Protocol) và REST API.

## Tổng quan

Máy chủ đồng bộ MCP Figma được thiết kế để tự động đồng bộ tài nguyên SVG từ file Figma vào repository sử dụng git. Máy chủ triển khai Model Context Protocol (MCP) và cung cấp REST API để quản lý quá trình đồng bộ.

### Tính năng chính

- 🔄 **Đồng bộ tự động**: Phát hiện thay đổi trong Figma và đồng bộ SVG
- 🎯 **Đánh giá dev-ready**: Đánh giá trạng thái sẵn sàng phát triển của nodes
- 📦 **Xử lý theo batch**: Tối ưu hóa hiệu suất với xử lý batch
- 🐙 **Tích hợp Git**: Tự động commit và push thay đổi
- 🌐 **REST API**: Endpoints để trigger sync, query status, manage config
- 🤖 **Hỗ trợ MCP**: Tích hợp với MCP clients

## Cài đặt

### Yêu cầu hệ thống

- Python 3.8+
- Git (tùy chọn, cho git integration)

### Cài đặt dependencies

1. Tạo virtual environment:

```bash
python -m venv venv
```

2. Activate virtual environment:

- Trên Windows:

```bash
venv\Scripts\activate
```

- Trên macOS/Linux:

```bash
source venv/bin/activate
```

3. Cài đặt dependencies (sau khi activate venv):

```bash
pip install -r requirements.txt
```

**Lưu ý**: Luôn activate virtual environment trước khi chạy bất kỳ lệnh nào liên quan đến project này để đảm bảo isolation và tránh conflicts với global packages.

### Cấu hình

1. Tạo file `.env` hoặc thiết lập biến môi trường:

```bash
# Figma API Token (bắt buộc)
FIGMA_API_TOKEN=your_figma_token_here

# Server config
HOST=localhost
PORT=8001

# Git integration (tùy chọn)
GIT_REPO_PATH=./repo
GIT_AUTO_COMMIT=true
GIT_AUTO_PUSH=true

# Logging
LOG_LEVEL=INFO
```

2. Cấu hình Figma:
   - Lấy API token từ Figma Account Settings
   - Đảm bảo file Figma được chia sẻ với token

## Sử dụng

### Chạy REST API Server

```bash
python -m server.main
```

Máy chủ sẽ chạy tại `http://localhost:8001`

### Chạy MCP Server

```bash
python -m server.mcp.server
```

### API Endpoints

#### Trigger Sync
```http
POST /api/v1/sync/trigger
Content-Type: application/json

{
  "file_key": "your-figma-file-key",
  "node_id": "root-node-id",
  "output_dir": "./output",
  "force_sync": false,
  "naming_filters": {
    "include_patterns": ["svg_export_*", "icon_*"],
    "exclude_patterns": ["temp_*", "draft_*"]
  }
}
```

#### Get Sync Status
```http
GET /api/v1/sync/{sync_id}/status
```

#### Get Configuration
```http
GET /api/v1/config
```

#### Update Configuration
```http
PUT /api/v1/config
Content-Type: application/json

{
  "figma": {
    "batch_size": 10,
    "delay_between_batches": 1.5
  }
}
```

### MCP Tools

Máy chủ cung cấp các MCP tools:

- `sync_figma_assets`: Đồng bộ assets từ Figma
- `get_sync_status`: Lấy trạng thái đồng bộ
- `list_sync_jobs`: Liệt kê các sync jobs

## Kiến trúc

```
Máy chủ đồng bộ MCP Figma
├── MCP Server Layer      # MCP protocol implementation
├── REST API Layer        # FastAPI endpoints
├── Figma Sync Service    # Core sync logic
├── Change Detector       # Phát hiện thay đổi
├── Dev Ready Detector    # Đánh giá dev-readiness
├── Git Integration       # Git operations
├── Background Worker     # Async processing
└── Configuration         # Centralized config
```

## Phát triển

### Cấu trúc thư mục

```
server/
├── __init__.py
├── main.py                 # FastAPI app entry point
├── config/
│   ├── __init__.py
│   └── settings.py         # Configuration management
├── services/
│   ├── __init__.py
│   ├── figma_sync.py       # Main sync service
│   ├── change_detector.py  # Change detection
│   ├── dev_ready_detector.py # Dev-readiness assessment
│   └── git_integration.py  # Git operations
├── api/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py      # API models
│   └── routes/             # API routes (future)
├── mcp/
│   ├── __init__.py
│   └── server.py           # MCP server implementation
├── workers/
│   ├── __init__.py
│   └── background_worker.py # Async job processing
└── utils/
    ├── __init__.py
    └── helpers.py          # Utility functions
```

### Chạy tests

Đảm bảo virtual environment đã được activate, sau đó:

```bash
pytest
```

### Code formatting

Đảm bảo virtual environment đã được activate, sau đó:

```bash
black server/
isort server/
```

## Quy tắc dự án

- Sử dụng tiếng Việt cho documentation
- Tuân thủ PEP 8 style guidelines
- Sử dụng type hints
- Comprehensive error handling
- Async/await cho I/O operations

## Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## Giấy phép

Dự án này được cấp phép theo Giấy phép MIT.

## Liên hệ

Đối với câu hỏi hoặc hỗ trợ, vui lòng mở issue trên GitHub.

---

**Version**: 1.0.0
**Date**: 2025-08-28
**Author**: Kilo Code