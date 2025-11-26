# FanqieQimaoDownloader

基于 Rain API V3 的番茄小说和七猫小说下载工具，支持批量下载和EPUB导出。

## 功能特性

- 🔍 支持番茄小说和七猫小说搜索
- 📥 批量下载小说章节
- 📖 自动生成EPUB电子书
- 🌐 现代Web界面 (FastAPI + Alpine.js)
- ⚡ 异步下载，支持并发控制
- 📊 实时进度跟踪和任务管理
- 🔒 速率限制保护 (每日200章节)
- 📱 响应式设计

## 快速开始

### 1. 环境要求

- Python 3.8+
- pip

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置API密钥

复制环境变量模板并填入你的API密钥：

```bash
cp .env.example .env
# 编辑 .env 文件，设置 RAIN_API_KEY
```

### 4. 初始化数据库

```bash
python init_db.py
```

### 5. 启动应用

```bash
python start.py
```

或者直接使用uvicorn：

```bash
uvicorn app.main:app --reload
```

访问 http://localhost:8000 开始使用。

## 项目结构

```
FanqieQimaoDownloader/
├── app/                          # 应用主目录
│   ├── api/                      # API客户端层
│   ├── models/                   # 数据模型层 (SQLAlchemy)
│   ├── services/                 # 业务逻辑层
│   ├── web/                      # Web层
│   │   ├── routes/               # API路由 (FastAPI)
│   │   └── templates/            # HTML模板 (Jinja2)
│   ├── utils/                    # 工具函数
│   └── config.py                 # 配置管理 (Pydantic)
├── data/                         # 数据存储目录
│   ├── books/                    # 书籍数据
│   ├── epubs/                    # 生成的EPUB文件
│   └── database.db               # SQLite数据库
├── tests/                        # 测试目录
├── reference/                    # API参考文档
├── alembic/                      # 数据库迁移
├── requirements.txt              # Python依赖
├── .env.example                  # 环境变量模板
└── README.md                     # 项目说明
```

## API使用说明

### 搜索书籍

```bash
GET /api/books/search?q={关键词}&platform={fanqie|qimao}&page={页码}
```

### 添加书籍

```bash
POST /api/books/{platform}/{book_id}
```

### 下载书籍

```bash
POST /api/tasks/{book_id}/download
```

### 查看任务状态

```bash
GET /api/tasks/{task_id}
```

## 开发状态

当前已完成 **Phase 1: 基础架构搭建**

- ✅ 项目架构设计
- ✅ 完整的目录结构
- ✅ 数据库模型 (SQLAlchemy)
- ✅ 配置管理 (Pydantic)
- ✅ Web框架基础 (FastAPI)
- ✅ 数据库迁移 (Alembic)

## 技术栈

- **Web框架**: FastAPI
- **数据库**: SQLAlchemy + SQLite
- **配置管理**: Pydantic Settings
- **前端**: Alpine.js + TailwindCSS
- **HTTP客户端**: httpx
- **EPUB生成**: ebooklib
- **图片处理**: Pillow

## 注意事项

- 免费版API限制每日下载200章节
- 请遵守相关法律法规，仅用于个人学习和研究
- API密钥请妥善保管，不要泄露到版本控制系统

## 许可证

MIT License
