"""
API 工具函数模块

提供各 API 客户端共用的工具方法
"""

import html
import re
from datetime import datetime
from typing import Any, List, Optional


def safe_int(value: Any, default: int = 0) -> int:
    """安全转换为整数
    
    Args:
        value: 要转换的值
        default: 转换失败时的默认值
        
    Returns:
        转换后的整数
    """
    if value is None:
        return default
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """安全转换为浮点数
    
    Args:
        value: 要转换的值
        default: 转换失败时的默认值
        
    Returns:
        转换后的浮点数
    """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def format_timestamp(timestamp: int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化时间戳为字符串
    
    Args:
        timestamp: Unix 时间戳
        fmt: 目标格式字符串
        
    Returns:
        格式化后的时间字符串，失败返回空字符串
    """
    if not timestamp:
        return ""
    try:
        return datetime.fromtimestamp(timestamp).strftime(fmt)
    except (ValueError, OSError, TypeError):
        return ""


def parse_datetime(date_str: str, formats: Optional[List[str]] = None) -> int:
    """解析多种格式的日期字符串为时间戳
    
    Args:
        date_str: 日期字符串
        formats: 尝试的格式列表，默认为常见格式
        
    Returns:
        Unix 时间戳，解析失败返回 0
    """
    if not date_str:
        return 0
    formats = formats or ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return int(datetime.strptime(date_str, fmt).timestamp())
        except Exception:
            continue
    return 0


def strip_html(text: str) -> str:
    """去除 HTML 标记并反转义
    
    Args:
        text: 包含 HTML 的文本
        
    Returns:
        清理后的纯文本
    """
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", "", text)
    return html.unescape(cleaned).strip()


def clean_content(content: str) -> str:
    """清理章节正文中的占位文本
    
    Args:
        content: 原始内容
        
    Returns:
        清理后的内容
    """
    if not content:
        return ""
    # 移除常见的占位文本
    cleaned = content.replace("<<---展开全部章节--->>", "")
    # 合并多余的空行
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()