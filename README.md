# Qisumi的书库

[![Version](https://img.shields.io/badge/version-1.6.3-blue.svg)](https://github.com/qisumi/fanqie-qimao-downloader/releases/tag/v1.6.3)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.x-brightgreen.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

基于 Rain API V3 的番茄小说、七猫小说和笔趣阁下载工具，支持批量下载和EPUB导出。

## ✨ 功能特性

- 🔍 **多平台搜索** - 支持番茄小说和七猫小说
- 📥 **智能下载** - 异步并发下载，自动重试
- 📖 **EPUB导出** - 自动生成标准EPUB电子书
- 🔄 **增量更新** - 检测并下载新章节
- 🌐 **现代界面** - Vue 3 + Naive UI 单页应用，响应式设计
- ⚡ **高性能** - 异步架构，并发控制
- 📊 **任务管理** - 实时进度跟踪
- 🔒 **密码保护** - 可选的访问密码保护
- 👥 **公共+私人书架** - 共用访问密码，可按用户名切换私人书架，公共书架与任务状态共享
- 🔐 **配额保护** - 自动速率限制（每日2000万字）
- 🌐 **PWA 支持** - 完整的PWA功能，包括安装提示、自动更新、离线支持和骨架屏加载效果

## 🖼️ 界面预览

- **首页**: 系统状态总览，快速访问入口
- **搜索**: 关键词搜索，一键添加书籍
- **书籍管理**: 查看详情、下载进度、EPUB导出
- **任务监控**: 下载任务状态跟踪

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/qisumi/fanqie-qimao-downloader.git
cd fanqie-qimao-downloader

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 RAIN_API_KEY

# 启动服务
docker-compose up -d
```

访问 http://localhost:4568 开始使用。

### 方式二：手动部署

#### 1. 环境要求

- Python 3.8+
- pip

#### 2. 安装依赖

```bash
git clone https://github.com/qisumi/fanqie-qimao-downloader.git
cd fanqie-qimao-downloader
pip install -r requirements.txt
```

#### 2.1 前端构建（可选）

本项目使用 Vue 3 + Naive UI 构建前端。前端资源已预构建。如果您需要修改前端代码，请按以下步骤重新构建：

1. 安装 Node.js (v18+)
2. 安装依赖并构建：

```bash
cd frontend
npm install
npm run build
```

构建产物将输出到 `frontend/dist/` 目录，后端会自动服务这些静态文件。

开发模式下，可以启动 Vite 开发服务器：

```bash
cd frontend
npm run dev
```

访问 `http://localhost:3000`，Vite 会自动代理 API 请求到后端。

#### 2.2 可选：生成 PWA 图标

项目包含一个图标生成脚本 `scripts/generate_icons.py`，用于从 SVG 或已有 PNG 生成常用的 PWA 图标（64x64、192x192、512x512）。

依赖（可选，Windows 上需先安装 Cairo 运行时）：
```powershell
pip install cairosvg
```

运行脚本：
```powershell
python scripts\generate_icons.py
```

生成的图标会保存在 `app/web/static/images/`，`manifest.json` 已配置为引用这些图标。


#### 3. 配置API密钥

复制环境变量模板并填入你的API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```ini
RAIN_API_KEY=你的API密钥
```

#### 4. 初始化数据库

```bash
python init_db.py
```

#### 5. 启动应用

```bash
python start.py
```

或者使用uvicorn：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 4568 --reload
```

访问 http://localhost:4568 开始使用。

## 📁 项目结构

```
FanqieQimaoDownloader/
├── app/                          # 后端应用主目录
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
│   │   └── static/               # 静态资源（图标等））
│   ├── utils/                    # 工具模块
│   │   ├── database.py           # 数据库连接
│   │   ├── rate_limiter.py       # 速率限制
│   │   └── logger.py             # 日志管理
│   ├── main.py                   # FastAPI入口
│   └── config.py                 # 配置管理
├── frontend/                     # Vue 3 前端项目
│   ├── src/                      # 源代码
│   │   ├── views/                # 页面组件
│   │   ├── components/           # 通用组件
│   │   ├── stores/               # Pinia 状态管理
│   │   ├── api/                  # API 封装
│   │   └── router/               # 路由配置
│   ├── dist/                     # 构建产物
│   └── package.json              # 前端依赖
├── data/                         # 数据存储
│   ├── books/                    # 书籍章节内容
│   ├── epubs/                    # EPUB文件
│   └── database.db               # SQLite数据库
├── tests/                        # 测试套件
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
- Swagger UI: http://localhost:4568/docs
- ReDoc: http://localhost:4568/redoc

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
curl "http://localhost:4568/api/books/search?q=斗罗大陆&platform=fanqie"
```

**添加书籍:**
```bash
curl -X POST "http://localhost:4568/api/books/fanqie/7123456789"
```

**开始下载:**
```bash
curl -X POST "http://localhost:4568/api/tasks/{book_uuid}/download"
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
HOST=127.0.0.1
PORT=4568
DEBUG=false  # 生产环境设为 false
LOG_LEVEL=INFO

# 密码保护 (可选)
APP_PASSWORD=your_password  # 留空则不启用
SECRET_KEY=your-secret-key  # 生产环境建议修改
SESSION_EXPIRE_HOURS=168    # 登录有效期: 7天
```

## PWA (Progressive Web App)

项目包含对 PWA 的完整支持（manifest、service worker、离线回退、安装与更新提示等），并提供安装/更新/离线横幅与统一的 `usePwaManager` 管理。

详细实现、调试与设计要点见：`docs/PWA_FEATURES.md`。

> 📖 完整部署指南请参阅 [DEPLOYMENT.md](DEPLOYMENT.md)

## 📊 开发状态

**当前版本: v1.6.1** 🎉

| 阶段 | 状态 | 描述 |
|------|------|------|
| Phase 1 | ✅ 完成 | 基础架构搭建 |
| Phase 2 | ✅ 完成 | API客户端实现 |
| Phase 3 | ✅ 完成 | 服务层实现 |
| Phase 4 | ✅ 完成 | Web层实现 |
| Phase 5 | ✅ 完成 | 功能完善 |
| Phase 6 | ✅ 完成 | 测试与优化 |
| Phase 7 | ✅ 完成 | 部署与发布 |
| Phase 8 | ✅ 完成 | Vue 3 前端迁移 |

> 📋 查看完整变更日志: [CHANGELOG.md](CHANGELOG.md)

## 🛠️ 技术栈

### 后端

| 组件 | 技术 | 版本 |
|------|------|------|
| Web框架 | FastAPI | ≥0.104.0 |
| ORM | SQLAlchemy | ≥2.0.0 |
| 数据库 | SQLite | - |
| HTTP客户端 | httpx | ≥0.25.0 |
| EPUB生成 | ebooklib | ≥0.18 |
| 图片处理 | Pillow | ≥10.0.0 |
| 数据验证 | Pydantic | ≥2.0.0 |

### 前端

| 组件 | 技术 | 版本 |
|------|------|------|
| 框架 | Vue 3 | ^3.4 |
| 构建工具 | Vite | ^5.0 |
| 路由 | Vue Router | ^4.2 |
| 状态管理 | Pinia | ^2.1 |
| UI组件库 | Naive UI | ^2.38 |
| HTTP客户端 | Axios | ^1.6 |

## ⚠️ 注意事项

1. **配额限制**: API每日限制下载2000万字
2. **合规使用**: 请遵守相关法律法规，仅用于个人学习研究
3. **密钥安全**: API密钥请妥善保管，不要提交到版本控制系统
4. **网络要求**: 确保能够正常访问 Rain API 服务

## 📚 文档

- [部署手册](DEPLOYMENT.md) - Windows/Linux 部署指南
- [变更日志](CHANGELOG.md) - 版本更新记录
- [API文档](http://localhost:4568/docs) - Swagger UI（启动后访问）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
