#!/usr/bin/env python3
"""
FanqieQimaoDownloader 启动脚本
"""

import sys
import subprocess
from pathlib import Path

def check_requirements():
    """检查依赖是否已安装"""
    try:
        import fastapi
        import sqlalchemy
        import uvicorn
        print("✅ 依赖检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def init_database():
    """初始化数据库"""
    print("正在初始化数据库...")
    try:
        subprocess.run([sys.executable, "init_db.py"], check=True)
        print("✅ 数据库初始化完成")
        return True
    except subprocess.CalledProcessError:
        print("❌ 数据库初始化失败")
        return False

def start_server():
    """启动Web服务器"""
    # 从配置文件读取 HOST 和 PORT
    from app.config import get_settings
    settings = get_settings()
    
    print("正在启动FanqieQimaoDownloader服务器...")
    print(f"访问 http://{settings.host}:{settings.port} 查看应用")
    print("按 Ctrl+C 停止服务器")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", str(settings.host),
            "--port", str(settings.port),
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except subprocess.CalledProcessError:
        print("❌ 服务器启动失败")

def main():
    """主函数"""
    print("🚀 FanqieQimaoDownloader v1.8.0")
    print("=" * 40)

    # 检查当前目录
    if not Path("app").exists():
        print("❌ 请在项目根目录下运行此脚本")
        sys.exit(1)

    # 检查依赖
    if not check_requirements():
        sys.exit(1)

    # 初始化数据库（如果不存在）
    if not Path("data/database.db").exists():
        if not init_database():
            sys.exit(1)

    # 启动服务器
    start_server()

if __name__ == "__main__":
    main()
