#!/bin/bash
# PM2 部署脚本 - FanqieQimaoDownloader

set -e

echo "=========================================="
echo "  FanqieQimaoDownloader PM2 部署脚本"
echo "=========================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"

# 检查 PM2
if ! command -v pm2 &> /dev/null; then
    echo "❌ 未找到 PM2，正在安装..."
    npm install -g pm2
fi

echo "✅ PM2 已安装"

# 检查依赖
echo ""
echo "📦 检查 Python 依赖..."
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate || source venv/Scripts/activate 2>/dev/null || true

pip install -q -r requirements.txt
echo "✅ Python 依赖已安装"

# 检查环境变量
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  未找到 .env 文件，正在创建..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请编辑配置后重新运行"
    echo "   编辑命令: nano .env 或 vim .env"
    exit 0
fi

# 初始化数据库
echo ""
echo "🗄️  初始化数据库..."
if [ ! -f "data/database.db" ]; then
    python3 init_db.py
    echo "✅ 数据库已初始化"
else
    echo "✅ 数据库已存在"
fi

# 构建前端
echo ""
echo "🔨 构建前端..."
if [ -d "frontend" ]; then
    cd frontend
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    npm run build
    cd ..
    echo "✅ 前端已构建"
else
    echo "⚠️  未找到 frontend 目录，跳过前端构建"
fi

# 创建日志目录
mkdir -p logs

# 停止旧进程
echo ""
echo "🛑 停止旧进程..."
pm2 stop fanqie-downloader 2>/dev/null || true
pm2 delete fanqie-downloader 2>/dev/null || true

# 启动新进程
echo ""
echo "🚀 启动应用..."
pm2 start ecosystem.config.js

# 保存进程列表
pm2 save

# 显示状态
echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
pm2 status
echo ""
echo "📝 常用命令:"
echo "   查看日志: pm2 logs fanqie-downloader"
echo "   查看状态: pm2 status"
echo "   重启应用: pm2 restart fanqie-downloader"
echo "   停止应用: pm2 stop fanqie-downloader"
echo "   监控应用: pm2 monit"
echo ""
echo "🌐 访问地址: http://127.0.0.1:4568"
echo "=========================================="
