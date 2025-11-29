# FanqieQimaoDownloader 部署手册

本文档详细介绍如何在 Windows 和 Linux 系统上部署 FanqieQimaoDownloader。

## 目录

- [环境要求](#环境要求)
- [快速部署](#快速部署)
- [详细部署步骤](#详细部署步骤)
  - [Windows 部署](#windows-部署)
  - [Linux 部署](#linux-部署)
- [配置说明](#配置说明)
- [生产环境配置](#生产环境配置)
- [日志管理](#日志管理)
- [常见问题](#常见问题)
- [维护与更新](#维护与更新)

---

## 环境要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| Python | 3.8+ | 3.10+ |
| 内存 | 512MB | 1GB+ |
| 磁盘空间 | 1GB | 10GB+ (取决于下载量) |
| 网络 | 可访问 Rain API | 稳定的网络连接 |

---

## 快速部署

```bash
# 1. 克隆项目
git clone https://github.com/qisumi/fanqie-qimao-downloader.git
cd fanqie-qimao-downloader

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入您的 Rain API 密钥

# 6. 初始化数据库
python init_db.py

# 7. 启动服务
python start.py
```

服务启动后访问 http://localhost:8000 即可使用。

---

## 详细部署步骤

### Windows 部署

#### 1. 安装 Python

1. 从 [Python 官网](https://www.python.org/downloads/) 下载 Python 3.10+
2. 运行安装程序，**勾选 "Add Python to PATH"**
3. 验证安装：
   ```powershell
   python --version
   pip --version
   ```

#### 2. 获取项目代码

```powershell
# 使用 Git 克隆
git clone https://github.com/qisumi/fanqie-qimao-downloader.git
cd fanqie-qimao-downloader

# 或者下载 ZIP 包解压
```

#### 3. 创建虚拟环境

```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 如果遇到执行策略限制，先运行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 4. 安装依赖

```powershell
# 升级 pip
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

#### 5. 配置环境变量

```powershell
# 复制配置模板
copy .env.example .env

# 使用记事本编辑
notepad .env
```

**必须修改的配置：**
```ini
RAIN_API_KEY=您的API密钥
```

**生产环境建议修改：**
```ini
DEBUG=false
RELOAD=false
LOG_LEVEL=INFO
```

#### 6. 初始化数据库

```powershell
python init_db.py
```

#### 7. 启动服务

```powershell
# 使用启动脚本（推荐）
python start.py

# 或直接使用 uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 8. 设置开机自启动（可选）

创建批处理文件 `start_server.bat`：
```batch
@echo off
cd /d D:\path\to\fanqie-qimao-downloader
call venv\Scripts\activate
python start.py
```

使用 Windows 任务计划程序设置开机启动。

---

### Linux 部署

#### 1. 安装 Python

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

**CentOS/RHEL:**
```bash
sudo yum install python3 python3-pip git
```

**验证安装：**
```bash
python3 --version
pip3 --version
```

#### 2. 获取项目代码

```bash
# 克隆项目
git clone https://github.com/qisumi/fanqie-qimao-downloader.git
cd fanqie-qimao-downloader
```

#### 3. 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

#### 4. 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

#### 5. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用 vim
```

**必须修改的配置：**
```ini
RAIN_API_KEY=您的API密钥
```

**生产环境建议修改：**
```ini
DEBUG=false
RELOAD=false
LOG_LEVEL=INFO
HOST=127.0.0.1  # 如果使用反向代理
```

#### 6. 初始化数据库

```bash
python init_db.py
```

#### 7. 启动服务

```bash
# 前台运行（测试用）
python start.py

# 后台运行
nohup python start.py > /dev/null 2>&1 &
```

#### 8. 配置 systemd 服务（推荐）

创建服务文件 `/etc/systemd/system/fanqie-downloader.service`：

```ini
[Unit]
Description=FanqieQimaoDownloader Web Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/fanqie-qimao-downloader
Environment="PATH=/opt/fanqie-qimao-downloader/venv/bin"
ExecStart=/opt/fanqie-qimao-downloader/venv/bin/python start.py
Restart=always
RestartSec=10

# 日志
StandardOutput=append:/var/log/fanqie-downloader/stdout.log
StandardError=append:/var/log/fanqie-downloader/stderr.log

[Install]
WantedBy=multi-user.target
```

**启用服务：**
```bash
# 创建日志目录
sudo mkdir -p /var/log/fanqie-downloader
sudo chown www-data:www-data /var/log/fanqie-downloader

# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start fanqie-downloader

# 设置开机自启
sudo systemctl enable fanqie-downloader

# 查看状态
sudo systemctl status fanqie-downloader

# 查看日志
sudo journalctl -u fanqie-downloader -f
```

#### 9. 配置 Nginx 反向代理（推荐）

安装 Nginx：
```bash
sudo apt install nginx  # Ubuntu/Debian
sudo yum install nginx  # CentOS/RHEL
```

创建配置文件 `/etc/nginx/sites-available/fanqie-downloader`：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为您的域名或 IP

    # 客户端最大上传大小
    client_max_body_size 100M;

    # 访问日志
    access_log /var/log/nginx/fanqie-downloader.access.log;
    error_log /var/log/nginx/fanqie-downloader.error.log;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件缓存
    location /static/ {
        alias /opt/fanqie-qimao-downloader/app/web/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

**启用配置：**
```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/fanqie-downloader /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重新加载 Nginx
sudo systemctl reload nginx
```

---

## 配置说明

### 必填配置

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `RAIN_API_KEY` | Rain API 密钥 | `abc123...` |

### 可选配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `RAIN_API_BASE_URL` | `http://v3.rain.ink` | API 基础 URL |
| `DATABASE_URL` | `sqlite:///./data/database.db` | 数据库连接字符串 |
| `DATA_DIR` | `./data` | 数据目录 |
| `BOOKS_DIR` | `./data/books` | 章节内容存储目录 |
| `EPUBS_DIR` | `./data/epubs` | EPUB 文件存储目录 |
| `DAILY_WORD_LIMIT` | `20000000` | 每日字数限制 (2000万) |
| `CONCURRENT_DOWNLOADS` | `3` | 并发下载数 |
| `DOWNLOAD_DELAY` | `0.5` | 下载间隔 (秒) |
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8000` | 监听端口 |
| `DEBUG` | `true` | 调试模式 |
| `RELOAD` | `true` | 热重载 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `LOG_FILE` | `./logs/app.log` | 日志文件路径 |
| `APP_PASSWORD` | (空) | 访问密码，留空不启用保护 |
| `SECRET_KEY` | (默认值) | Cookie签名密钥 |
| `SESSION_EXPIRE_HOURS` | `168` | 登录有效期(小时) |

---

## 生产环境配置

### 推荐的 .env 配置

```ini
# API 配置
RAIN_API_KEY=您的API密钥
RAIN_API_BASE_URL=http://v3.rain.ink
API_TIMEOUT=30
API_RETRY_TIMES=3

# 数据库配置
DATABASE_URL=sqlite:///./data/database.db

# 存储配置
DATA_DIR=./data
BOOKS_DIR=./data/books
EPUBS_DIR=./data/epubs

# 下载限制
DAILY_WORD_LIMIT=20000000
CONCURRENT_DOWNLOADS=3
DOWNLOAD_DELAY=0.5

# 服务配置 - 生产环境
HOST=127.0.0.1
PORT=8000
DEBUG=false
RELOAD=false

# 密码保护 - 生产环境强烈建议启用
APP_PASSWORD=your_secure_password
SECRET_KEY=change-this-to-a-random-string-in-production
SESSION_EXPIRE_HOURS=168

# 日志配置 - 生产环境
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
```

### 安全建议

1. **不要将 `.env` 文件提交到版本控制**
2. **使用强密码保护服务器**
3. **配置防火墙，仅开放必要端口**
4. **使用 HTTPS**（通过 Nginx + Let's Encrypt）
5. **定期备份数据库和下载的内容**

### 备份策略

```bash
# 创建备份脚本 backup.sh
#!/bin/bash
BACKUP_DIR="/backup/fanqie-downloader"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
cp /opt/fanqie-qimao-downloader/data/database.db $BACKUP_DIR/database_$DATE.db

# 备份 EPUB 文件（可选）
tar -czf $BACKUP_DIR/epubs_$DATE.tar.gz /opt/fanqie-qimao-downloader/data/epubs/

# 保留最近 7 天的备份
find $BACKUP_DIR -mtime +7 -delete

echo "Backup completed: $DATE"
```

添加到 crontab：
```bash
# 每天凌晨 3 点备份
0 3 * * * /opt/fanqie-qimao-downloader/backup.sh >> /var/log/fanqie-backup.log 2>&1
```

---

## 日志管理

### 日志位置

| 日志类型 | 位置 |
|----------|------|
| 应用日志 | `./logs/app.log` |
| systemd 日志 | `journalctl -u fanqie-downloader` |
| Nginx 访问日志 | `/var/log/nginx/fanqie-downloader.access.log` |
| Nginx 错误日志 | `/var/log/nginx/fanqie-downloader.error.log` |

### 日志级别

| 级别 | 说明 |
|------|------|
| `DEBUG` | 详细调试信息（仅开发环境使用） |
| `INFO` | 常规信息（推荐生产环境使用） |
| `WARNING` | 警告信息 |
| `ERROR` | 错误信息 |
| `CRITICAL` | 严重错误 |

### 日志轮转

应用内置日志轮转功能：
- 单个日志文件最大 10MB（可通过 `LOG_MAX_SIZE` 配置）
- 保留 5 个备份文件（可通过 `LOG_BACKUP_COUNT` 配置）

---

## 常见问题

### Q1: 启动时提示 "RAIN_API_KEY" 未配置

**原因：** 未设置 API 密钥

**解决：**
1. 复制 `.env.example` 为 `.env`
2. 编辑 `.env`，填入您的 Rain API 密钥

### Q2: 数据库初始化失败

**原因：** 数据目录权限问题

**解决：**
```bash
# Linux
sudo chown -R $USER:$USER ./data
chmod -R 755 ./data

# Windows
# 确保当前用户对 data 目录有读写权限
```

### Q3: 无法访问 Web 界面

**检查步骤：**
1. 确认服务已启动：`python start.py`
2. 检查端口是否被占用：
   ```bash
   # Linux
   netstat -tlnp | grep 8000
   # Windows
   netstat -an | findstr 8000
   ```
3. 检查防火墙设置
4. 如果使用 Nginx，检查反向代理配置

### Q4: 下载速度慢

**可能原因：**
1. 网络连接不稳定
2. 并发数设置过低

**解决：**
```ini
# 增加并发数（注意 API 限制）
CONCURRENT_DOWNLOADS=5

# 减少下载间隔
DOWNLOAD_DELAY=0.3
```

### Q5: 配额用尽

**原因：** 达到每日 2000 万字下载限制

**解决：** 等待第二天配额重置，或检查是否有不必要的重复下载

### Q6: EPUB 生成失败

**可能原因：**
1. 章节内容未完全下载
2. 磁盘空间不足

**解决：**
1. 检查书籍下载状态是否为 "completed"
2. 检查磁盘空间
3. 查看日志获取详细错误信息

---

## 维护与更新

### 更新项目

```bash
# 停止服务
sudo systemctl stop fanqie-downloader  # Linux
# 或 Ctrl+C 停止前台进程

# 拉取最新代码
git pull origin master

# 更新依赖
source venv/bin/activate  # 或 venv\Scripts\activate
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 重启服务
sudo systemctl start fanqie-downloader  # Linux
# 或 python start.py
```

### 数据库迁移

```bash
# 查看当前版本
alembic current

# 升级到最新版本
alembic upgrade head

# 回滚一个版本（谨慎使用）
alembic downgrade -1
```

### 清理缓存

```bash
# 清理 Python 缓存
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# 清理日志（保留最近的）
find ./logs -name "*.log.*" -mtime +30 -delete
```

---

## 技术支持

如遇到问题，请：

1. 查看日志文件获取详细错误信息
2. 检查 [常见问题](#常见问题) 部分
3. 在 GitHub Issues 中搜索相关问题
4. 提交新的 Issue，并附上：
   - 操作系统版本
   - Python 版本
   - 错误日志
   - 复现步骤

---

**祝您使用愉快！** 📚
