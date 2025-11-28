"""
日志配置模块

提供统一的日志配置，支持：
- 控制台彩色输出
- 文件日志轮转
- 不同模块的日志级别配置
- 结构化日志格式
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


# ANSI颜色代码
class LogColors:
    """日志颜色定义"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # 日志级别颜色
    DEBUG = "\033[36m"      # 青色
    INFO = "\033[32m"       # 绿色
    WARNING = "\033[33m"    # 黄色
    ERROR = "\033[31m"      # 红色
    CRITICAL = "\033[35m"   # 紫色
    
    # 其他元素颜色
    TIMESTAMP = "\033[90m"  # 灰色
    NAME = "\033[34m"       # 蓝色
    MESSAGE = "\033[0m"     # 默认


class ColoredFormatter(logging.Formatter):
    """
    彩色日志格式化器
    
    为不同级别的日志添加颜色
    """
    
    LEVEL_COLORS = {
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
    }
    
    def __init__(self, fmt: str = None, datefmt: str = None, use_colors: bool = True):
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        # 保存原始值
        original_levelname = record.levelname
        original_msg = record.msg
        original_name = record.name
        
        if self.use_colors:
            # 添加颜色
            level_color = self.LEVEL_COLORS.get(record.levelno, LogColors.RESET)
            
            record.levelname = f"{level_color}{record.levelname:8}{LogColors.RESET}"
            record.name = f"{LogColors.NAME}{record.name}{LogColors.RESET}"
            
            # 如果是异常，保持原始消息
            if not record.exc_info:
                record.msg = f"{LogColors.MESSAGE}{record.msg}{LogColors.RESET}"
        
        # 格式化
        result = super().format(record)
        
        # 恢复原始值
        record.levelname = original_levelname
        record.msg = original_msg
        record.name = original_name
        
        return result


class LoggerManager:
    """
    日志管理器
    
    负责初始化和配置应用程序的日志系统
    """
    
    # 默认配置
    DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
    
    _instance: Optional["LoggerManager"] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if LoggerManager._initialized:
            return
        LoggerManager._initialized = True
        
        self._handlers = []
        self._root_logger = logging.getLogger()
    
    def setup(
        self,
        level: str = "INFO",
        log_file: Optional[str] = None,
        log_format: Optional[str] = None,
        date_format: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        use_colors: bool = True,
        enable_console: bool = True,
    ) -> None:
        """
        配置日志系统
        
        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: 日志文件路径，None表示不输出到文件
            log_format: 日志格式
            date_format: 日期格式
            max_file_size: 单个日志文件最大大小（字节）
            backup_count: 保留的备份文件数量
            use_colors: 是否在控制台使用彩色输出
            enable_console: 是否输出到控制台
        """
        # 清除现有处理器
        self._cleanup()
        
        # 设置日志级别
        log_level = getattr(logging, level.upper(), logging.INFO)
        self._root_logger.setLevel(log_level)
        
        # 使用的格式
        console_format = log_format or self.DEFAULT_FORMAT
        file_format = log_format or self.DEFAULT_FILE_FORMAT
        date_fmt = date_format or self.DEFAULT_DATE_FORMAT
        
        # 添加控制台处理器
        if enable_console:
            self._add_console_handler(console_format, date_fmt, log_level, use_colors)
        
        # 添加文件处理器
        if log_file:
            self._add_file_handler(
                log_file, file_format, date_fmt, log_level, 
                max_file_size, backup_count
            )
        
        # 设置第三方库的日志级别（减少噪音）
        self._configure_third_party_loggers()
        
        logging.info(f"日志系统初始化完成 - 级别: {level}, 文件: {log_file or '无'}")
    
    def _add_console_handler(
        self, 
        fmt: str, 
        datefmt: str, 
        level: int,
        use_colors: bool
    ) -> None:
        """添加控制台处理器"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # 检测是否支持颜色（Windows CMD可能不支持）
        supports_color = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        formatter = ColoredFormatter(fmt, datefmt, use_colors and supports_color)
        handler.setFormatter(formatter)
        
        self._root_logger.addHandler(handler)
        self._handlers.append(handler)
    
    def _add_file_handler(
        self,
        log_file: str,
        fmt: str,
        datefmt: str,
        level: int,
        max_size: int,
        backup_count: int
    ) -> None:
        """添加文件处理器（带轮转）"""
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用RotatingFileHandler实现大小轮转
        handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        handler.setLevel(level)
        
        # 文件日志不使用颜色
        formatter = logging.Formatter(fmt, datefmt)
        handler.setFormatter(formatter)
        
        self._root_logger.addHandler(handler)
        self._handlers.append(handler)
    
    def _configure_third_party_loggers(self) -> None:
        """配置第三方库的日志级别，减少噪音"""
        # 将一些verbose的第三方库设置为WARNING级别
        noisy_loggers = [
            "httpx",
            "httpcore",
            "urllib3",
            "asyncio",
            "sqlalchemy.engine",
            "alembic",
        ]
        
        for logger_name in noisy_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    def _cleanup(self) -> None:
        """清理现有的处理器"""
        for handler in self._handlers:
            self._root_logger.removeHandler(handler)
            handler.close()
        self._handlers.clear()
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的logger
        
        Args:
            name: logger名称，通常使用 __name__
            
        Returns:
            配置好的logger实例
        """
        return logging.getLogger(name)
    
    def set_level(self, level: str, logger_name: Optional[str] = None) -> None:
        """
        动态设置日志级别
        
        Args:
            level: 日志级别
            logger_name: logger名称，None表示设置根logger
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        if logger_name:
            logging.getLogger(logger_name).setLevel(log_level)
        else:
            self._root_logger.setLevel(log_level)


# 全局日志管理器实例
_logger_manager: Optional[LoggerManager] = None


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    use_colors: bool = True,
    enable_console: bool = True,
) -> LoggerManager:
    """
    初始化日志系统（便捷函数）
    
    Args:
        level: 日志级别
        log_file: 日志文件路径
        log_format: 日志格式
        date_format: 日期格式
        max_file_size: 单个日志文件最大大小
        backup_count: 保留备份数量
        use_colors: 是否使用彩色输出
        enable_console: 是否输出到控制台
        
    Returns:
        LoggerManager实例
    """
    global _logger_manager
    _logger_manager = LoggerManager()
    _logger_manager.setup(
        level=level,
        log_file=log_file,
        log_format=log_format,
        date_format=date_format,
        max_file_size=max_file_size,
        backup_count=backup_count,
        use_colors=use_colors,
        enable_console=enable_console,
    )
    return _logger_manager


def get_logger(name: str) -> logging.Logger:
    """
    获取logger的便捷函数
    
    Args:
        name: logger名称，通常使用 __name__
        
    Returns:
        Logger实例
    """
    return logging.getLogger(name)


def init_from_settings() -> LoggerManager:
    """
    从应用配置初始化日志系统
    
    从 app.config.settings 读取配置并初始化日志
    """
    from app.config import get_settings
    
    settings = get_settings()
    
    return setup_logging(
        level=settings.log_level,
        log_file=settings.log_file,
        max_file_size=settings.log_max_size,
        backup_count=settings.log_backup_count,
        use_colors=True,
        enable_console=True,
    )


# 为了兼容性，提供一个简单的日志装饰器
def log_function_call(logger: Optional[logging.Logger] = None):
    """
    装饰器：记录函数调用
    
    Args:
        logger: 使用的logger，None则使用函数所在模块的logger
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or logging.getLogger(func.__module__)
            _logger.debug(f"调用 {func.__name__}(args={args}, kwargs={kwargs})")
            
            try:
                result = func(*args, **kwargs)
                _logger.debug(f"{func.__name__} 返回: {result}")
                return result
            except Exception as e:
                _logger.exception(f"{func.__name__} 异常: {e}")
                raise
        
        return wrapper
    return decorator


def log_async_function_call(logger: Optional[logging.Logger] = None):
    """
    装饰器：记录异步函数调用
    
    Args:
        logger: 使用的logger，None则使用函数所在模块的logger
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            _logger = logger or logging.getLogger(func.__module__)
            _logger.debug(f"调用 {func.__name__}(args={args}, kwargs={kwargs})")
            
            try:
                result = await func(*args, **kwargs)
                _logger.debug(f"{func.__name__} 返回: {result}")
                return result
            except Exception as e:
                _logger.exception(f"{func.__name__} 异常: {e}")
                raise
        
        return wrapper
    return decorator
