# Hướng dẫn chạy Tool Export và Demo với dữ liệu thực tế

## Tổng quan

Tool export của dự án này cho phép đồng bộ và export tài nguyên SVG từ Figma một cách tự động với các tính năng nâng cao:

- **Phát hiện thay đổi**: Chỉ export những thành phần đã thay đổi
- **Đánh giá dev-ready**: Đánh giá trạng thái sẵn sàng phát triển
- **Xử lý batch**: Tối ưu hóa hiệu suất với xử lý theo batch
- **Lọc naming**: Export có chọn lọc dựa trên pattern tên
- **Tích hợp Git**: Tự động commit và push (tùy chọn)

## Yêu cầu hệ thống

- Python 3.8+
- Virtual environment (khuyến nghị)
- Figma API Token
- File key của project Figma cần export

## Cài đặt và Chuẩn bị

### 1. Tạo Virtual Environment

```bash
# Tạo virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### 2. Cài đặt Dependencies

```bash
# Sau khi activate venv
pip install -r requirements.txt
```

### 3. Cấu hình Environment Variables

Tạo file `.env` trong thư mục gốc với nội dung sau:

```bash
# Figma API Configuration (BẮT BUỘC)
FIGMA_API_TOKEN=your_figma_api_token_here
FIGMA_FILE_KEY=your_figma_file_key_here

# Output Configuration
GITHUB_DATA_PATH=./exports/

# Server Configuration
HOST=localhost
PORT=8001

# Git Integration (TUỲ CHỌN)
GIT_REPO_PATH=./repo
GIT_REMOTE_NAME=origin
GIT_BRANCH=main
GIT_AUTO_COMMIT=true
GIT_AUTO_PUSH=true

# Sync Configuration
SYNC_CACHE_DURATION=3600
SYNC_DEV_READY_THRESHOLD=0.8
SYNC_FORCE_SYNC_ALLOWED=true

# Logging
LOG_LEVEL=INFO
```

#### Cách lấy FIGMA_API_TOKEN:

1. Đăng nhập vào Figma
2. Vào **Settings** > **Account** > **Personal access tokens**
3. Tạo token mới với quyền **Read** (đủ cho export)
4. Copy token và paste vào `.env`

#### Cách lấy FIGMA_FILE_KEY:

1. Mở file Figma cần export
2. Trong URL: `https://www.figma.com/file/[FILE_KEY]/[FILE_NAME]`
3. Copy phần `[FILE_KEY]` (thường là chuỗi dài với dấu gạch ngang)
4. Paste vào `.env`

## Cách chạy Tool Export

### Phương pháp 1: Chạy Demo Script (Khuyến nghị)

Script demo sẽ chạy export hoàn chỉnh và hiển thị kết quả chi tiết:

```bash
# Đảm bảo đã activate venv
python scripts/demo_export_and_show.py
```

**Script sẽ thực hiện:**
- Kiểm tra FIGMA_FILE_KEY từ .env
- Khởi tạo FigmaSyncService
- Export tất cả nodes từ root (node_id: "0:1")
- Phát hiện thay đổi và dev-ready status
- Lưu SVG files và metadata
- Tạo báo cáo tổng hợp
- Hiển thị kết quả chi tiết

### Phương pháp 2: Chạy Test với dữ liệu thực

```bash
# Chạy test với naming filters cụ thể
python test/test_export_real.py
```

**Điểm khác biệt:**
- Output vào thư mục `./test/exports`
- Force sync = True (export tất cả)
- Áp dụng naming filters: chỉ export nodes có tên bắt đầu với "svg_export_*" hoặc "icon_*"

### Phương pháp 3: Sử dụng trực tiếp Service (Advanced)

```python
import asyncio
from server.services.figma_sync import FigmaSyncService

async def custom_export():
    service = FigmaSyncService()

    result = await service.process_sync(
        file_key="your-file-key",
        node_id="0:1",  # Root node
        output_dir="./custom_output",
        force_sync=False,  # Chỉ export changed items
        naming_filters={
            "include_patterns": ["*"],  # Export tất cả
            "exclude_patterns": ["temp_*", "draft_*"],
            "case_sensitive": False
        }
    )

    print(f"Export completed: {result}")

# Chạy
asyncio.run(custom_export())
```

## Giải thích Output và Kết quả

### Cấu trúc thư mục output

```
exports/
├── cache/
│   └── figma_export_cache.json    # Cache cho change detection
├── ready_button_primary.svg       # SVG files với prefix status
├── ready_icon_arrow.json          # Metadata cho mỗi SVG
├── draft_component_temp.svg
├── export_report.json             # Báo cáo chi tiết JSON
├── export_summary.md              # Báo cáo tóm tắt Markdown
└── ...
```

### Các loại files được tạo

1. **SVG Files**: Files hình ảnh vector
   - Tên file: `{status}_{name}_{node_id}.svg`
   - Status: `ready_`, `approved_`, `draft_`, hoặc không có prefix

2. **JSON Metadata**: Thông tin chi tiết cho mỗi SVG
   - Chứa: kích thước, vị trí, dev-ready score, issues, export settings

3. **Báo cáo tổng hợp**:
   - `export_report.json`: Báo cáo chi tiết tất cả nodes
   - `export_summary.md`: Tóm tắt dễ đọc

### Thông tin hiển thị trong console

```
DEMO: Export Figma and Show Files
============================================================

[FILE] File Key: abc123-def456-ghi789
[PATH] Output Path: ./exports/

[INIT] Initializing FigmaSyncService...

[CONFIG] Export Configuration:
   Root Node: 0:1
   Force Sync: True
   Filters: {'include_patterns': ['*'], 'exclude_patterns': [], 'case_sensitive': False}

[SUCCESS] Export completed!
[RESULT] {'exported': 15, 'failed': 0, 'skipped': 0, 'dev_ready': 12, 'needs_review': 3, ...}

[FILES] Files in ./exports/:
   Total files: 32
   SVG files: 15
   JSON metadata: 15
   Markdown reports: 2

[SVG] Created SVG Files:
   1. ready_button_primary.svg (2048 bytes)
   2. ready_icon_arrow.svg (1024 bytes)
   3. draft_component_temp.svg (3072 bytes)
   ...
```

## Tùy chỉnh Export

### Naming Filters

```python
naming_filters = {
    "include_patterns": ["svg_export_*", "icon_*", "button_*"],
    "exclude_patterns": ["temp_*", "draft_*", "old_*"],
    "case_sensitive": False
}
```

### Export Types

- **Tất cả nodes**: `include_patterns: ["*"]`
- **Chỉ SVG exports**: `include_patterns: ["svg_export_*"]`
- **Chỉ icons**: `include_patterns: ["icon_*"]`
- **Buttons và components**: `include_patterns: ["button_*", "component_*"]`

### Force Sync Options

- `force_sync=True`: Export tất cả nodes (không kiểm tra thay đổi)
- `force_sync=False`: Chỉ export nodes đã thay đổi (mặc định)

## Troubleshooting

### Lỗi thường gặp

#### 1. "FIGMA_FILE_KEY not found in .env"

**Nguyên nhân**: Thiếu FIGMA_FILE_KEY trong file .env

**Giải pháp**:
- Kiểm tra file .env có tồn tại
- Thêm dòng: `FIGMA_FILE_KEY=your_file_key_here`
- Lấy file key từ URL Figma

#### 2. "Failed to get file information"

**Nguyên nhân**:
- FIGMA_API_TOKEN không hợp lệ
- File Figma không được chia sẻ với token
- Mạng hoặc rate limit

**Giải pháp**:
- Kiểm tra token trong Figma Settings
- Đảm bảo file được chia sẻ (Share > Anyone with link)
- Chờ 60 giây nếu bị rate limit

#### 3. "No files created"

**Nguyên nhân**:
- Không có nodes nào thỏa mãn criteria
- Tất cả nodes đã được export (không có thay đổi)

**Giải pháp**:
- Kiểm tra naming filters
- Sử dụng `force_sync=True` để export tất cả
- Kiểm tra console log để xem nodes được tìm thấy

#### 4. "Export failed" hoặc timeout

**Nguyên nhân**:
- Kết nối mạng không ổn định
- File Figma quá lớn
- Rate limit từ Figma API

**Giải pháp**:
- Giảm batch_size trong config
- Tăng delay_between_batches
- Chạy lại sau vài phút

### Debug Mode

Thêm vào `.env` để có log chi tiết:

```bash
LOG_LEVEL=DEBUG
```

### Kiểm tra Cache

Xóa cache để force full export:

```bash
rm -rf exports/cache/
```

## Ví dụ thực tế

### Export tất cả icons và buttons

```bash
# Trong .env
FIGMA_FILE_KEY=abc123-def456-ghi789
GITHUB_DATA_PATH=./exports/
```

```python
# custom_export.py
import asyncio
from server.services.figma_sync import FigmaSyncService

async def export_icons_buttons():
    service = FigmaSyncService()

    result = await service.process_sync(
        file_key="abc123-def456-ghi789",
        node_id="0:1",
        output_dir="./exports",
        force_sync=True,
        naming_filters={
            "include_patterns": ["icon_*", "button_*"],
            "exclude_patterns": ["temp_*", "draft_*"],
            "case_sensitive": False
        }
    )

    print(f"Exported {result['exported']} icons and buttons")

asyncio.run(export_icons_buttons())
```

### Kết quả mẫu

```
[FILES] Files in ./exports/:
   Total files: 24
   SVG files: 12
   JSON metadata: 12
   Markdown reports: 2

[SVG] Created SVG Files:
   1. ready_icon_arrow.svg (1024 bytes)
   2. ready_button_primary.svg (2048 bytes)
   3. ready_icon_search.svg (896 bytes)
   4. approved_button_secondary.svg (1536 bytes)
   ...
```

## Performance Tips

1. **Batch Size**: Giảm xuống 5-10 cho files lớn
2. **Delay**: Tăng lên 2-3 giây giữa batches
3. **Filters**: Sử dụng include_patterns để giảm số lượng nodes
4. **Cache**: Giữ cache để tăng tốc incremental exports

## Kết luận

Tool export này cung cấp giải pháp hoàn chỉnh để đồng bộ tài nguyên từ Figma với khả năng tùy chỉnh cao và xử lý lỗi robust. Sử dụng demo script để bắt đầu nhanh, sau đó tùy chỉnh theo nhu cầu cụ thể của project.