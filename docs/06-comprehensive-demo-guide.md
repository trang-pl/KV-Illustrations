# Comprehensive Demo Guide
Hướng dẫn sử dụng Comprehensive Test Script cho Figma SVG Export

## Tổng quan

Comprehensive Demo Script (`test/test_comprehensive_demo.py`) được thiết kế để demo và so sánh hai chế độ export chính:

- **Prefix Naming Mode**: Export theo pattern tên (ví dụ: `svg_exporter_*`)
- **Node ID Mode**: Export từ node ID cụ thể (ví dụ: `353-2712`)

## Tính năng chính

### 🔍 Environment Validation
- Kiểm tra FIGMA_API_TOKEN và FIGMA_FILE_KEY
- Validate format và permissions
- Báo cáo issues chi tiết

### 📊 Dual Mode Testing
- **Prefix Mode**: Test multiple patterns song song
- **Node ID Mode**: Test multiple node IDs với fallback
- Performance tracking cho từng test

### 📈 Comprehensive Reporting
- So sánh performance giữa hai modes
- Detailed analytics và recommendations
- JSON và Markdown reports

### 🛡️ Error Handling
- Graceful failure handling
- Detailed error reporting
- Recovery strategies

## Cách sử dụng

### 1. Chuẩn bị Environment

Tạo file `.env` với thông tin Figma:

```bash
# Figma API Configuration
FIGMA_API_TOKEN=your_figma_api_token_here
FIGMA_FILE_KEY=your_figma_file_key_here

# Optional configurations
HOST=localhost
PORT=8001
```

### 2. Chạy Demo

#### Cách 1: Chạy trực tiếp
```bash
cd /path/to/project
python test/test_comprehensive_demo.py
```

#### Cách 2: Sử dụng Demo Runner
```bash
cd /path/to/project
python run_comprehensive_demo.py
```

### 3. Kiểm tra Kết quả

Demo sẽ tạo output trong:
```
test/exports/comprehensive_demo/
├── prefix_mode_20250101_120000/
│   ├── svg_exporter_all/
│   ├── icon_all/
│   ├── component_all/
│   └── asset_all/
├── node_id_mode_20250101_120000/
│   ├── node_0_1/
│   ├── node_1_2/
│   └── node_2_3/
├── comprehensive_demo_report.json
└── comprehensive_demo_summary.md
```

## Cấu hình

### Default Configuration

```python
config = ComprehensiveConfig(
    # Environment variables (từ .env)
    figma_token=os.environ.get('FIGMA_API_TOKEN'),
    file_key=os.environ.get('FIGMA_FILE_KEY'),

    # Test settings
    force_sync=True,
    batch_size=10,
    delay_between_batches=1.0,

    # Prefix patterns
    prefix_patterns=[
        "svg_exporter_*",
        "icon_*",
        "component_*",
        "asset_*"
    ],

    # Node ID targets
    node_id_targets=[
        "0:1",      # Root node
        "1:2",      # Common page node
        "2:3",      # Common frame node
    ]
)
```

### Tùy chỉnh Configuration

Bạn có thể modify `ComprehensiveConfig` để:

- Thay đổi prefix patterns
- Thêm/bớt node ID targets
- Điều chỉnh batch size và delays
- Tùy chỉnh output directories

## Output Files

### 1. JSON Report (`comprehensive_demo_report.json`)
```json
{
  "comprehensive_demo_report": {
    "timestamp": "2025-01-01T12:00:00",
    "configuration": {...},
    "prefix_mode_summary": {
      "total_patterns": 4,
      "successful_patterns": 3,
      "total_exported": 25,
      "total_time": 45.67
    },
    "node_id_mode_summary": {
      "total_nodes": 3,
      "successful_nodes": 2,
      "total_exported": 18,
      "total_time": 32.45
    },
    "comparison": {
      "winner": "prefix_mode",
      "winner_reason": "Higher export count",
      "recommendations": [...]
    }
  }
}
```

### 2. Markdown Summary (`comprehensive_demo_summary.md`)
```markdown
# Comprehensive Demo Report

**Generated:** 2025-01-01 12:00:00

## Configuration
- File Key: `abc123...`
- Force Sync: true
- Batch Size: 10
- Prefix Patterns: svg_exporter_*, icon_*, component_*, asset_*
- Node ID Targets: 0:1, 1:2, 2:3

## Results Summary

### Prefix Mode
- Patterns Tested: 4
- Successful: 3
- Total Exported: 25
- Total Time: 45.67s

### Node ID Mode
- Nodes Tested: 3
- Successful: 2
- Total Exported: 18
- Total Time: 32.45s

## Comparison
**Winner:** Prefix Mode
**Reason:** Higher export count

## Recommendations
- Use prefix mode for bulk exports with naming conventions
- Use node ID mode for targeted exports from specific components
- Consider combining both modes for comprehensive coverage
```

### 3. SVG Files và Metadata

Mỗi exported asset bao gồm:
- **SVG file**: Vector graphic
- **JSON metadata**: Chi tiết về asset, dev-ready status, export settings

## Troubleshooting

### Common Issues

#### 1. Missing Environment Variables
```
ERROR: Missing environment variable: FIGMA_API_TOKEN
```
**Solution**: Tạo file `.env` với token hợp lệ

#### 2. Invalid File Key
```
ERROR: FIGMA_FILE_KEY contains invalid characters
```
**Solution**: Kiểm tra file key format (should be alphanumeric + hyphens)

#### 3. API Rate Limiting
```
ERROR: Rate limited - waiting...
```
**Solution**: Tăng `delay_between_batches` trong config

#### 4. No Exportable Assets
```
WARNING: No files were exported
```
**Solution**:
- Kiểm tra naming conventions trong Figma
- Verify node IDs tồn tại
- Check file permissions

### Debug Mode

Để chạy với debug output:
```bash
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import asyncio
from test.test_comprehensive_demo import run_comprehensive_demo
asyncio.run(run_comprehensive_demo())
"
```

## Performance Optimization

### Batch Size Tuning
- **Small batches (5-10)**: More reliable, slower
- **Large batches (20-50)**: Faster, more prone to rate limits

### Delay Optimization
- **Short delays (0.5-1s)**: Faster execution
- **Long delays (2-5s)**: More reliable, avoid rate limits

### Pattern Selection
- **Broad patterns**: `*_` (catches more, but slower)
- **Specific patterns**: `svg_export_*` (faster, more targeted)

## Best Practices

### 1. Environment Setup
- Luôn sử dụng virtual environment
- Keep `.env` file secure (không commit)
- Test với small file trước khi scale up

### 2. Figma File Organization
- Sử dụng consistent naming conventions
- Group related assets logically
- Use frames/components for better export results

### 3. Monitoring & Maintenance
- Review export reports regularly
- Monitor API usage và rate limits
- Update patterns dựa trên project evolution

## Integration với CI/CD

### GitHub Actions Example
```yaml
name: Figma Export Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run comprehensive demo
        run: python test/test_comprehensive_demo.py
        env:
          FIGMA_API_TOKEN: ${{ secrets.FIGMA_API_TOKEN }}
          FIGMA_FILE_KEY: ${{ secrets.FIGMA_FILE_KEY }}
```

## Support

### File Structure
```
test/
├── test_comprehensive_demo.py    # Main demo script
├── run_comprehensive_demo.py     # Simple runner
└── exports/
    └── comprehensive_demo/       # Output directory
```

### Related Files
- `server/services/figma_sync.py`: Core sync service
- `config/settings.py`: Configuration management
- `server/utils/node_id_converter.py`: Node ID utilities

---

**Version**: 1.0.0
**Last Updated**: 2025-01-01
**Author**: Kilo Code