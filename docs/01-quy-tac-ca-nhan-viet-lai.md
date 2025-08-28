# AI Agent Personal Rules - Rewritten for AI-to-AI Clarity

## 1. Ngôn ngữ và Giao tiếp (Language & Communication)

### Rule 1.1: Language Standard
- **Primary Language**: Tiếng Việt cho tất cả documentation và communication
- **Technical Terms**: Giữ nguyên thuật ngữ tiếng Anh không dịch
- **AI-to-AI Context**: Khi AI Agent giao tiếp với nhau, sử dụng tiếng Việt nhưng preserve English technical terms để tránh ambiguity

### Rule 1.2: User Context
- **User Profile**: Product Designer
- **Priority Focus**: Usability-first approach trong mọi solution
- **AI Agent Responsibility**: Luôn filter recommendations qua lens của Product Designer workflow

## 2. Workflow và Hiệu suất (Workflow & Performance)

### Rule 2.1: 80/20 Principle
- **Definition**: Tập trung 80% effort vào 20% tasks có impact cao nhất
- **AI Agent Implementation**: 
  - Identify high-impact tasks trước khi execute
  - Prioritize solutions có immediate usability benefits
  - Avoid over-engineering cho edge cases

### Rule 2.2: Model Context Protocol (MCP) Priority
- **Requirement**: Ưu tiên MCP workflow trong mọi tình huống
- **AI Agent Action**: 
  - Suggest MCP services khi possible
  - Help define MCP configurations cho long-term optimization
  - Document MCP setups trong /config/ directory

## 3. Tổ chức Tài liệu (Documentation Organization)

### Rule 3.1: Analysis Documents (/docs/)
- **Location**: /docs/ directory với hierarchy không quá 3 levels
- **Naming Convention**: `{index}-{descriptive-name}.md`
  - Index: 01, 02, 03... để maintain order
  - Descriptive name: kebab-case Vietnamese + English terms
- **Content Rule**: Ngắn gọn đủ ý, làm cơ sở cho AI Agent execution
- **Index Requirement**: Update index links sau mỗi document creation

### Rule 3.2: Reports (/reports/)
- **Location**: /reports/ directory
- **Naming Convention**: `{YYYY-MM-DD_HHMMSS}-{report-type}-{description}.md`
- **Content**: Detailed reports với timestamp và clear naming

## 4. Environment và Dependencies Management

### Rule 4.1: Environment Isolation
- **Principle**: Mọi dependencies cài trong environment riêng biệt
- **AI Agent Rule**: Luôn activate environment trước khi run tasks
- **Global Installation**: STRICTLY FORBIDDEN để avoid version conflicts

### Rule 4.2: Dependencies Strategy
- **Tool-Specific**: Mỗi tool có dependencies riêng
- **Isolation**: Không share dependencies giữa tools
- **AI Agent Verification**: Check environment activation trước mọi command execution

## 5. Configuration Management

### Rule 5.1: Centralized Config
- **Location**: /config/ directory
- **Structure**: Tool-specific config files
- **Hard-coding**: FORBIDDEN - tất cả parameters qua config

### Rule 5.2: Script Versioning & Pipeline Organization
- **Single Script**: `{index}-{script-name}-v{version}.{ext}`
  - Example: `01-dependency-setup-v1.2.py`
- **Pipeline Scripts**: `{index}.{sub-index}.{pipeline-name}_{step-name}.{ext}`
  - Master: `03-start-server-env.bat`
  - Steps: `03.1-start-server-env_cleanup.bat`, `03.2-start-server-env_start-mcp.bat`
- **AI Agent Responsibility**: Maintain version tracking và pipeline organization cho script changes
- **Server Ports**: 
  - MCP Server: `localhost:8001` (fixed)
  - N8N Server: `localhost:5678` (fixed)
  - API Documentation: `localhost:8001/docs`
  - Database API: `localhost:8001/api/v1/database/*`

## 6. Development Environment Rules

### Rule 6.1: N8N Development Setup
- **NO DOCKER**: Trong development environment, KHÔNG sử dụng Docker containers
- **Direct Installation**: Cài đặt N8N trực tiếp với npm để development thuận tiện
- **Local Server**: Chạy N8N server local để debug và test workflows
- **AI Agent Action**: Luôn check local installation trước khi suggest Docker alternatives

### Rule 6.2: Project Context Awareness  
- **README First**: LUÔN đọc README.md để hiểu current project state trước khi tạo mới
- **Structure Respect**: Tuân thủ existing project structure trong README
- **AI Agent Responsibility**: Reference README context khi suggest solutions

### Rule 6.3: Test File Organization
- **Location**: TẤT CẢ test files phải tạo trong `/test/` directory ở root level
- **No Scatter**: Không tạo test files scattered trong project directories
- **Structure**: `/test/{category}/{test-name}.{ext}`
- **AI Agent Enforcement**: Redirect mọi test file creation về `/test/` directory

## 7. Figma Plugin Development

### Rule 7: Figma Plugin Index
- **Documentation**: Tất cả hướng dẫn chi tiết về Figma Plugin development
- **manifest**: Figma chỉ sử dụng tên "manifest.json". Trước khi sửa manifest.json, tạo backup: manifest-backup-{YYYY-MM-DD_HHMMSS}.json. Khi có issue, restore từ backup ngay.
- **networkAccess**: sử dụng localhost, thêm port cụ thể nếu cần
"networkAccess": {
    "allowedDomains": ["none"],
    "devAllowedDomains": [
      "http://localhost",
      "https://localhost"
    ]
  }
## AI-to-AI Interaction Guidelines

### Context Sharing
1. **Rule Reference**: Luôn reference specific rule number khi communicate
2. **Environment Context**: Share current directory state và environment status
3. **Task State**: Clear về current task progress và dependencies

### Conflict Resolution
1. **Rule Priority**: Personal rules > General instructions
2. **Environment Constraints**: Windows PowerShell context awareness
3. **User Profile**: Product Designer priorities override generic solutions

