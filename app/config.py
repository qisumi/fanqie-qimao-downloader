"""
配置管理模块
使用Pydantic Settings管理环境变量和配置
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # API配置
    rain_api_key: str = "YOUR_API_KEY_HERE"
    rain_api_base_url: str = "http://v3.rain.ink"
    api_timeout: int = 30
    api_retry_times: int = 3

    # 数据库配置 (SQLite)
    database_url: str = "sqlite:///./data/database.db"

    # 存储配置
    data_dir: str = "./data"
    books_dir: str = "./data/books"
    epubs_dir: str = "./data/epubs"

    # 下载限制
    daily_chapter_limit: int = 200
    concurrent_downloads: int = 3
    download_delay: float = 0.5

    # Web服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    reload: bool = True

    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = "./logs/app.log"

    # EPUB配置
    epub_language: str = "zh-CN"
    epub_publisher: str = "FanqieQimaoDownloader"
    epub_cover_width: int = 600
    epub_cover_height: int = 800

    class Config:
        env_file = ".env"
        extra = "ignore"  # 忽略额外的环境变量

    @property
    def data_path(self) -> Path:
        """数据目录路径"""
        return Path(self.data_dir)

    @property
    def books_path(self) -> Path:
        """书籍存储目录路径"""
        return Path(self.books_dir)

    @property
    def epubs_path(self) -> Path:
        """EPUB存储目录路径"""
        return Path(self.epubs_dir)

    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.data_path,
            self.books_path,
            self.epubs_path,
            Path("./logs") if self.log_file else None
        ]

        for directory in directories:
            if directory and not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)


# 创建全局配置实例
_settings: Settings | None = None


def get_settings() -> Settings:
    """获取配置实例 (单例模式)"""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_directories()
    return _settings


# 向后兼容: 保留settings变量
settings = get_settings()