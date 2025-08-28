# Hướng dẫn Tổ chức Báo cáo (/reports/)

## Quy tắc Đặt tên Báo cáo

Tất cả các báo cáo trong thư mục `/reports/` phải tuân thủ quy tắc đặt tên sau:

```
{YYYY-MM-DD_HHMMSS}-{report-type}-{description}.md
```

### Giải thích các thành phần:

- **YYYY-MM-DD_HHMMSS**: Timestamp theo định dạng năm-tháng-ngày_giờphútgiây (ví dụ: 2025-08-28_040849)
- **report-type**: Loại báo cáo (ví dụ: weekly, monthly, bug-report, feature-summary)
- **description**: Mô tả ngắn gọn về nội dung báo cáo, sử dụng kebab-case (ví dụ: progress-summary, error-analysis)

### Ví dụ tên file:

- `2025-08-28_040849-weekly-progress-summary.md`
- `2025-08-28_120000-monthly-feature-report.md`
- `2025-08-28_150000-bug-analysis-login-issue.md`

## Mẫu Template cho Báo cáo

Dưới đây là mẫu template cho một báo cáo. Bạn có thể sao chép và điều chỉnh cho từng báo cáo cụ thể:

```markdown
# Tiêu đề Báo cáo

## Tổng quan
[ Mô tả ngắn gọn về mục đích và phạm vi của báo cáo ]

## Chi tiết
[ Nội dung chi tiết của báo cáo ]

### Phần 1: [Tên phần]
- [Điểm chính 1]
- [Điểm chính 2]

### Phần 2: [Tên phần]
- [Điểm chính 1]
- [Điểm chính 2]

## Kết luận
[ Tổng kết và khuyến nghị ]

## Metadata
- **Ngày tạo**: YYYY-MM-DD HH:MM:SS UTC
- **Tác giả**: [Tên tác giả]
- **Loại báo cáo**: [report-type]
- **Tags**: [tag1, tag2, tag3]
```

## Lưu ý
- Luôn sử dụng timestamp chính xác khi tạo file
- Giữ mô tả ngắn gọn nhưng đủ ý
- Sử dụng tiếng Việt cho nội dung chính, giữ nguyên thuật ngữ kỹ thuật tiếng Anh