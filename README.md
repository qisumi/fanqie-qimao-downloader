# FanqieQimaoDownloader

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/qisumi/fanqie-qimao-downloader/releases/tag/v1.0.0)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

基于 Rain API V3 的番茄小说和七猫小说下载工具，支持批量下载和EPUB导出。

## ✨ 功能特性

- 🔍 **多平台搜索** - 支持番茄小说和七猫小说
- 📥 **智能下载** - 异步并发下载，自动重试
- 📖 **EPUB导出** - 自动生成标准EPUB电子书
- 🔄 **增量更新** - 检测并下载新章节
- 🌐 **现代界面** - 响应式Web界面，支持移动端
- ⚡ **高性能** - 异步架构，并发控制
- 📊 **任务管理** - 实时进度跟踪
- 🔒 **配额保护** - 自动速率限制（每日2000万字）

## 🖼️ 界面预览

- **首页**: 系统状态总览，快速访问入口
- **搜索**: 关键词搜索，一键添加书籍
- **书籍管理**: 查看详情、下载进度、EPUB导出
- **任务监控**: 下载任务状态跟踪

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- pip

### 2. 安装依赖

```bash
git clone https://github.com/qisumi/fanqie-qimao-downloader.git
cd fanqie-qimao-downloader
pip install -r requirements.txt
```

### 3. 配置API密钥

复制环境变量模板并填入你的API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```ini
RAIN_API_KEY=你的API密钥
```

### 4. 初始化数据库

```bash
python init_db.py
```

### 5. 启动应用

```bash
python start.py
```

或者使用uvicorn：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 http://localhost:8000 开始使用。

## 📁 项目结构

```
FanqieQimaoDownloader/
├── app/                          # 应用主目录
│   ├── api/                      # Rain API客户端封装
│   │   ├── base.py               # 基类和异常定义
│   │   ├── fanqie.py             # 番茄小说API
│   │   └── qimao.py              # 七猫小说API
│   ├── models/                   # 数据模型 (SQLAlchemy ORM)
│   │   ├── book.py               # 书籍模型
│   │   ├── chapter.py            # 章节模型
│   │   ├── task.py               # 下载任务模型
│   │   └── quota.py              # 配额模型
│   ├── services/                 # 业务逻辑层
│   │   ├── book_service.py       # 书籍管理
│   │   ├── download_service.py   # 下载管理
│   │   ├── epub_service.py       # EPUB生成
│   │   └── storage_service.py    # 文件存储
│   ├── web/                      # Web层
│   │   ├── routes/               # API路由
│   │   └── templates/            # Jinja2模板
│   ├── utils/                    # 工具模块
│   │   ├── database.py           # 数据库连接
│   │   ├── rate_limiter.py       # 速率限制
│   │   └── logger.py             # 日志管理
│   ├── main.py                   # FastAPI入口
│   └── config.py                 # 配置管理
├── data/                         # 数据存储
│   ├── books/                    # 书籍章节内容
│   ├── epubs/                    # EPUB文件
│   └── database.db               # SQLite数据库
├── tests/                        # 测试套件 (85个测试)
│   ├── test_api/                 # API客户端测试
│   ├── test_services/            # 服务层测试
│   ├── test_web/                 # Web层测试
│   └── test_e2e/                 # 端到端测试
├── reference/                    # API参考文档
├── alembic/                      # 数据库迁移
├── requirements.txt              # Python依赖
└── README.md                     # 项目说明
```

## 📖 API文档

启动应用后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要API端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/books/search` | GET | 搜索书籍 |
| `/api/books/{platform}/{book_id}` | POST | 添加书籍 |
| `/api/books/` | GET | 获取书籍列表 |
| `/api/books/{id}` | GET | 获取书籍详情 |
| `/api/books/{id}` | DELETE | 删除书籍 |
| `/api/books/{id}/epub` | POST | 生成EPUB |
| `/api/tasks/{book_id}/download` | POST | 开始下载 |
| `/api/tasks/{book_id}/update` | POST | 更新书籍 |
| `/api/tasks/{id}` | GET | 获取任务状态 |
| `/api/stats/` | GET | 系统统计 |
| `/health` | GET | 健康检查 |

### 使用示例

**搜索书籍:**
```bash
curl "http://localhost:8000/api/books/search?q=斗罗大陆&platform=fanqie"
```

**添加书籍:**
```bash
curl -X POST "http://localhost:8000/api/books/fanqie/7123456789"
```

**开始下载:**
```bash
curl -X POST "http://localhost:8000/api/tasks/{book_uuid}/download"
```

## 🧪 测试

运行测试套件（85个测试用例）：

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试模块
pytest tests/test_api/ -v           # API客户端测试
pytest tests/test_services/ -v      # 服务层测试
pytest tests/test_web/ -v           # Web层测试
pytest tests/test_e2e/ -v           # 端到端测试

# 运行测试并生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

## ⚙️ 配置选项

在 `.env` 文件中可配置以下选项（详见 `.env.example`）：

```ini
# API配置 (必填)
RAIN_API_KEY=你的API密钥
RAIN_API_BASE_URL=http://v3.rain.ink
API_TIMEOUT=30
API_RETRY_TIMES=3

# 数据库配置
DATABASE_URL=sqlite:///./data/database.db

# 下载限制
DAILY_WORD_LIMIT=20000000  # 每日字数限制: 2000万字
CONCURRENT_DOWNLOADS=3
DOWNLOAD_DELAY=0.5

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=false  # 生产环境设为 false
LOG_LEVEL=INFO
```

> 📖 完整部署指南请参阅 [DEPLOYMENT.md](DEPLOYMENT.md)

## 📊 开发状态

**当前版本: v1.0.0** 🎉

| 阶段 | 状态 | 描述 |
|------|------|------|
| Phase 1 | ✅ 完成 | 基础架构搭建 |
| Phase 2 | ✅ 完成 | API客户端实现 |
| Phase 3 | ✅ 完成 | 服务层实现 |
| Phase 4 | ✅ 完成 | Web层实现 |
| Phase 5 | ✅ 完成 | 功能完善 |
| Phase 6 | ✅ 完成 | 测试与优化（85测试） |
| Phase 7 | ✅ 完成 | 部署与发布 |

> 📋 查看完整变更日志: [CHANGELOG.md](CHANGELOG.md)

## 🛠️ 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| Web框架 | FastAPI | ≥0.104.0 |
| ORM | SQLAlchemy | ≥2.0.0 |
| 数据库 | SQLite | - |
| HTTP客户端 | httpx | ≥0.25.0 |
| EPUB生成 | ebooklib | ≥0.18 |
| 图片处理 | Pillow | ≥10.0.0 |
| 数据验证 | Pydantic | ≥2.0.0 |
| 前端框架 | Alpine.js | 3.x |
| CSS框架 | TailwindCSS | 2.x |

## ⚠️ 注意事项

1. **配额限制**: API每日限制下载2000万字
2. **合规使用**: 请遵守相关法律法规，仅用于个人学习研究
3. **密钥安全**: API密钥请妥善保管，不要提交到版本控制系统
4. **网络要求**: 确保能够正常访问 Rain API 服务

## 📚 文档

- [部署手册](DEPLOYMENT.md) - Windows/Linux 部署指南
- [变更日志](CHANGELOG.md) - 版本更新记录
- [API文档](http://localhost:8000/docs) - Swagger UI（启动后访问）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
