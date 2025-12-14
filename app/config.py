"""
配置管理模块
使用Pydantic Settings管理环境变量和配置
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # 忽略额外的环境变量
    )

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
    txts_dir: str = "./data/txts"

    # 下载限制
    daily_word_limit: int = 20000000  # 每日字数限制: 2000万字
    concurrent_downloads: int = 3
    download_delay: float = 0.5

    # Web服务配置
    host: str = "127.0.0.1"
    port: int = 4568
    debug: bool = True
    reload: bool = True

    # 密码保护配置
    app_password: Optional[str] = None  # 应用密码，为空则不启用密码保护
    secret_key: str = "fanqie-qimao-downloader-secret-key-change-in-production"  # Cookie签名密钥
    session_expire_hours: int = 168  # 登录有效期: 7天 (7*24=168小时)

    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = "./logs/app.log"
    log_max_size: int = 10 * 1024 * 1024  # 10MB 单个日志文件最大大小
    log_backup_count: int = 5  # 保留的备份文件数量
    log_format: Optional[str] = None  # 自定义日志格式，None使用默认格式

    # EPUB配置
    epub_language: str = "zh-CN"
    epub_publisher: str = "FanqieQimaoDownloader"
    epub_cover_width: int = 600
    epub_cover_height: int = 800

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

    @property
    def txts_path(self) -> Path:
        """TXT存储目录路径"""
        return Path(self.txts_dir)

    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.data_path,
            self.books_path,
            self.epubs_path,
            self.txts_path,
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