# Qisumi的书库

[![Version](https://img.shields.io/badge/version-1.7.1-blue.svg)](https://github.com/qisumi/fanqie-qimao-downloader/releases/tag/v1.7.1)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.x-brightgreen.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

基于 Rain API V3 的网络小说下载工具，支持番茄小说、七猫小说和笔趣阁平台，提供批量下载、EPUB/TXT导出和在线阅读功能。

## ✨ 功能特性

### � 下载与导出
- **多平台支持** - 番茄小说、七猫小说、笔趣阁
- **智能下载** - 异步并发下载，自动重试，断点续传
- **EPUB导出** - 自动生成标准EPUB电子书
- **TXT导出** - 支持合并章节为TXT文件
- **增量更新** - 检测并下载新章节
- **本地上传** - 支持上传本地TXT/EPUB文件并解析分章

### 📖 阅读体验
- **在线阅读器** - 内置阅读器，支持翻页和滚动模式
- **阅读设置** - 字体、字号、主题、行距、页边距可调
- **阅读进度** - 自动保存，跨设备同步
- **书签功能** - 支持添加和管理书签

### � 界面与交互
- **现代界面** - Vue 3 + Naive UI 单页应用
- **响应式设计** - 完美支持桌面和移动端
- **深色模式** - 浅色/深色/跟随系统三种主题
- **PWA支持** - 可安装为桌面应用，支持离线使用

### 👥 多用户与安全
- **公共+私人书架** - 公共书架共享，私人书架按用户隔离
- **密码保护** - 可选的访问密码保护
- **配额保护** - 自动速率限制（每日2000万字，笔趣阁豁免）

### ⚡ 高性能
- **异步架构** - 基于 FastAPI 的高性能后端
- **WebSocket** - 下载进度实时推送
- **智能缓存** - 多层缓存策略优化加载速度

## 🖼️ 界面预览

- **首页** - 系统状态总览，快速访问入口
- **搜索** - 关键词搜索，一键添加书籍
- **书架** - 公共/私人书架管理，筛选与排序
- **书籍详情** - 章节热力图，范围下载，导出操作
- **阅读器** - 翻页/滚动模式，阅读设置
- **任务监控** - 下载任务状态实时跟踪
- **设置** - 用户管理，主题切换

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
- Node.js 18+（仅开发时需要）

#### 2. 安装后端依赖

```bash
git clone https://github.com/qisumi/fanqie-qimao-downloader.git
cd fanqie-qimao-downloader
pip install -r requirements.txt
```

#### 3. 配置API密钥

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

或者使用 uvicorn：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 4568 --reload
```

访问 http://localhost:4568 开始使用。

### 前端开发（可选）

前端资源已预构建。如需修改前端代码：

```bash
cd frontend
npm install
npm run dev    # 开发模式，访问 http://localhost:3000
npm run build  # 构建生产版本
```

## 📁 项目结构

```
FanqieQimaoDownloader/
├── app/                          # 后端应用主目录
│   ├── api/                      # Rain API 客户端封装
│   │   ├── base.py               # 基类和异常定义
│   │   ├── fanqie.py             # 番茄小说 API
│   │   ├── qimao.py              # 七猫小说 API
│   │   └── biquge.py             # 笔趣阁 API
│   ├── models/                   # 数据模型 (SQLAlchemy ORM)
│   │   ├── book.py               # 书籍模型
│   │   ├── chapter.py            # 章节模型
│   │   ├── task.py               # 下载任务模型
│   │   ├── quota.py              # 配额模型
│   │   ├── user.py               # 用户模型
│   │   ├── user_book.py          # 用户书架关联
│   │   ├── bookmark.py           # 书签模型
│   │   ├── reading_progress.py   # 阅读进度
│   │   └── reading_history.py    # 阅读历史
│   ├── services/                 # 业务逻辑层
│   │   ├── book/                 # 书籍管理 (mixin 模块)
│   │   ├── download/             # 下载管理 (mixin 模块)
│   │   ├── reader/               # 阅读器服务
│   │   ├── storage/              # 文件存储
│   │   ├── epub_service.py       # EPUB 生成
│   │   ├── txt_service.py        # TXT 生成
│   │   └── user_service.py       # 用户管理
│   ├── web/                      # Web 层
│   │   ├── routes/               # API 路由
│   │   │   ├── books_*.py        # 书籍相关 API
│   │   │   ├── tasks_*.py        # 任务相关 API
│   │   │   ├── users.py          # 用户管理 API
│   │   │   └── ws.py             # WebSocket 路由
│   │   └── static/               # 静态资源
│   ├── main.py                   # FastAPI 入口
│   └── config.py                 # 配置管理
├── frontend/                     # Vue 3 前端项目
│   ├── src/
│   │   ├── views/                # 页面组件
│   │   │   ├── HomeView.vue      # 首页
│   │   │   ├── SearchView.vue    # 搜索页
│   │   │   ├── BooksView.vue     # 书架页
│   │   │   ├── BookDetailView.vue # 书籍详情
│   │   │   ├── ReaderView.vue    # 阅读器
│   │   │   ├── TasksView.vue     # 任务管理
│   │   │   ├── SettingsView.vue  # 设置页
│   │   │   └── LoginView.vue     # 登录页
│   │   ├── components/           # 通用组件
│   │   ├── composables/          # Vue Composables
│   │   ├── stores/               # Pinia 状态管理
│   │   ├── api/                  # API 封装
│   │   ├── pwa/                  # PWA 相关
│   │   └── router/               # 路由配置
│   └── dist/                     # 构建产物
├── data/                         # 数据存储
│   ├── books/                    # 书籍章节内容
│   ├── epubs/                    # EPUB 文件
│   ├── txts/                     # TXT 文件
│   └── database.db               # SQLite 数据库
├── tests/                        # 测试套件
│   ├── test_api/                 # API 客户端测试
│   ├── test_services/            # 服务层测试
│   ├── test_web/                 # Web 层测试
│   └── test_e2e/                 # 端到端测试
├── alembic/                      # 数据库迁移
├── scripts/                      # 辅助脚本
├── reference/                    # API 参考文档
├── requirements.txt              # Python 依赖
├── docker-compose.yml            # Docker 编排
└── README.md                     # 项目说明
```

## 📖 API 文档

启动应用后访问：
- Swagger UI: http://localhost:4568/docs
- ReDoc: http://localhost:4568/redoc

### 主要 API 端点

#### 书籍管理

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/books/search` | GET | 搜索书籍 |
| `/api/books/{platform}/{book_id}` | POST | 添加书籍 |
| `/api/books/` | GET | 获取书籍列表 |
| `/api/books/{id}` | GET | 获取书籍详情 |
| `/api/books/{id}` | DELETE | 删除书籍 |
| `/api/books/{id}/status` | GET | 获取书籍状态（轻量） |
| `/api/books/{id}/epub` | POST | 生成 EPUB |
| `/api/books/{id}/epub/download` | GET | 下载 EPUB |
| `/api/books/{id}/txt` | POST | 生成 TXT |
| `/api/books/{id}/txt/download` | GET | 下载 TXT |
| `/api/books/upload` | POST | 上传本地书籍 |

#### 阅读器

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/books/{id}/reader/chapters` | GET | 获取阅读章节列表 |
| `/api/books/{id}/reader/chapters/{idx}/content` | GET | 获取章节内容 |
| `/api/books/{id}/reader/progress` | GET/POST | 阅读进度 |
| `/api/books/{id}/reader/bookmarks` | GET/POST/DELETE | 书签管理 |

#### 任务管理

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/tasks/{book_id}/download` | POST | 开始下载 |
| `/api/tasks/{book_id}/update` | POST | 更新书籍 |
| `/api/tasks/{id}` | GET | 获取任务状态 |
| `/api/tasks/{id}/cancel` | POST | 取消任务 |
| `/api/tasks/quota` | GET | 获取配额信息 |

#### 用户管理

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/users/` | GET | 获取用户列表 |
| `/api/users/` | POST | 创建用户 |
| `/api/users/{id}` | PUT | 更新用户 |
| `/api/users/{id}` | DELETE | 删除用户 |
| `/api/users/{id}/books` | GET | 获取用户私人书架 |

#### WebSocket

| 端点 | 描述 |
|------|------|
| `/ws/tasks/{task_id}` | 订阅任务进度 |
| `/ws/books/{book_id}` | 订阅书籍下载进度 |

#### 其他

| 端点 | 方法 | 描述 |
|------|------|------|
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

**范围下载:**
```bash
curl -X POST "http://localhost:4568/api/tasks/{book_uuid}/download?start_chapter=0&end_chapter=99"
```

## 🧪 测试

运行测试套件：

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试模块
pytest tests/test_api/ -v           # API 客户端测试
pytest tests/test_services/ -v      # 服务层测试
pytest tests/test_web/ -v           # Web 层测试
pytest tests/test_e2e/ -v           # 端到端测试

# 运行测试并生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

## ⚙️ 配置选项

在 `.env` 文件中可配置以下选项（详见 `.env.example`）：

```ini
# API 配置 (必填)
RAIN_API_KEY=你的API密钥
RAIN_API_BASE_URL=http://v3.rain.ink
API_TIMEOUT=30
API_RETRY_TIMES=3

# 数据库配置
DATABASE_URL=sqlite:///./data/database.db

# 下载限制
DAILY_WORD_LIMIT=20000000    # 每日字数限制: 2000万字
CONCURRENT_DOWNLOADS=3
DOWNLOAD_DELAY=0.5

# 服务配置
HOST=127.0.0.1
PORT=4568
DEBUG=false                  # 生产环境设为 false
LOG_LEVEL=INFO

# 密码保护 (可选)
APP_PASSWORD=your_password   # 留空则不启用
SECRET_KEY=your-secret-key   # 生产环境建议修改
SESSION_EXPIRE_HOURS=168     # 登录有效期: 7天
```

## 🛠️ 技术栈

### 后端

| 组件 | 技术 | 版本 |
|------|------|------|
| Web 框架 | FastAPI | ≥0.104.0 |
| ORM | SQLAlchemy | ≥2.0.0 |
| 数据库 | SQLite | - |
| HTTP 客户端 | httpx | ≥0.25.0 |
| EPUB 生成 | ebooklib | ≥0.18 |
| 图片处理 | Pillow | ≥10.0.0 |
| 数据验证 | Pydantic | ≥2.0.0 |
| 日志 | structlog | ≥23.1.0 |

### 前端

| 组件 | 技术 | 版本 |
|------|------|------|
| 框架 | Vue 3 | ^3.4 |
| 构建工具 | Vite | ^5.4 |
| 路由 | Vue Router | ^4.6 |
| 状态管理 | Pinia | ^2.3 |
| UI 组件库 | Naive UI | ^2.43 |
| HTTP 客户端 | Axios | ^1.13 |
| PWA | vite-plugin-pwa + Workbox | ^0.17 / ^7.4 |

## ⚠️ 注意事项

1. **配额限制**: API 每日限制下载 2000 万字（笔趣阁平台豁免）
2. **合规使用**: 请遵守相关法律法规，仅用于个人学习研究
3. **密钥安全**: API 密钥请妥善保管，不要提交到版本控制系统
4. **网络要求**: 确保能够正常访问 Rain API 服务

## 📚 文档

- [部署手册](DEPLOYMENT.md) - Windows/Linux 部署指南
- [变更日志](CHANGELOG.md) - 版本更新记录
- [路线图](ROADMAP.md) - 功能规划
- [API 文档](http://localhost:4568/docs) - Swagger UI（启动后访问）

## 📊 开发状态

**当前版本: v1.7.1** 🎉

| 阶段 | 状态 | 描述 |
|------|------|------|
| Phase 1 | ✅ 完成 | 基础架构搭建 |
| Phase 2 | ✅ 完成 | API 客户端实现 |
| Phase 3 | ✅ 完成 | 服务层实现 |
| Phase 4 | ✅ 完成 | Web 层实现 |
| Phase 5 | ✅ 完成 | 功能完善 |
| Phase 6 | ✅ 完成 | 测试与优化 |
| Phase 7 | ✅ 完成 | 部署与发布 |
| Phase 8 | ✅ 完成 | Vue 3 前端迁移 |
| Phase 9 | ✅ 完成 | 在线阅读器 |
| Phase 10 | ✅ 完成 | 多用户与本地上传 |

> 📋 查看完整变更日志: [CHANGELOG.md](CHANGELOG.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 鸣谢与赞助

非常感谢所有为本项目贡献代码、测试、文档及反馈的朋友。

如果你或你的组织愿意赞助本项目以支持持续开发与托管费用，请联系我们或在本仓库中提交 Issue，我们会在此处列出赞助者与支持方式。

### 赞助者 / 鸣谢

| 姓名 / 昵称 | 贡献类型 | 说明 |
|---|---|---|
| 哈哈 | 测试 & 打赏 |  |
| leibudao | 测试 |  |
| caizw | 测试 |  |
| zoey_pointer | 测试 |  |
