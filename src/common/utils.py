"""
通用工具函数
时间转换、MD5 生成、文件操作等
"""
import hashlib
import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional, Union

# 日期格式模板
DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y.%m.%d",
    "%b %d, %Y",
    "%B %d, %Y",
    "%Y年%m月%d日",
]

DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y/%m/%d %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%y %H:%M:%S",
    "%m/%d/%Y %I:%M:%S %p",
    "%d-%m-%Y %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%Y.%m.%d %H:%M:%S",
    "%a, %d %b %Y %H:%M:%S %z",
]


def generate_id(*fields) -> str:
    """
    根据字段组合生成唯一 ID（MD5）

    Args:
        *fields: 用于生成 ID 的字段

    Returns:
        MD5 哈希值
    """
    data = json.dumps(fields, sort_keys=True, default=str)
    return hashlib.md5(data.encode()).hexdigest()


def parse_datetime(
    value: Union[str, int, float, datetime, date],
    fmt: Optional[str] = None,
) -> Optional[datetime]:
    """
    智能解析日期时间

    Args:
        value: 日期时间值
        fmt: 指定格式（可选）

    Returns:
        datetime 对象，解析失败返回 None
    """
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    if not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    # 尝试指定格式
    if fmt:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    # 尝试 ISO 格式
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass

    # 尝试所有已知格式
    for fmt in DATETIME_FORMATS + DATE_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            return dt
        except ValueError:
            continue

    return None


def cost_minutes(time_str: str) -> Optional[int]:
    """
    将时间差字符串转换为分钟

    支持格式:
    - "2:28" (2小时28分钟)
    - "1d2h30m" (1天2小时30分钟)
    - "2h30m" (2小时30分钟)
    - "90m" (90分钟)
    - "3h" (3小时)

    Args:
        time_str: 时间差字符串

    Returns:
        分钟数，解析失败返回 None
    """
    if not time_str:
        return None

    time_str = str(time_str).strip()

    # 格式: "2:28" (小时:分钟)
    if ":" in time_str:
        try:
            hours, minutes = map(int, time_str.split(":"))
            return hours * 60 + minutes
        except (ValueError, AttributeError):
            pass

    # 格式: "1d2h30m"
    pattern = r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?"
    match = re.match(pattern, time_str)
    if match:
        days, hours, minutes = match.groups()
        total = 0
        if days:
            total += int(days) * 24 * 60
        if hours:
            total += int(hours) * 60
        if minutes:
            total += int(minutes)
        return total if total > 0 else None

    return None


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在

    Args:
        path: 目录路径

    Returns:
        目录 Path 对象
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_file(path: Union[str, Path], encoding: str = "utf-8") -> str:
    """
    读取文件内容

    Args:
        path: 文件路径
        encoding: 编码格式

    Returns:
        文件内容
    """
    with open(path, "r", encoding=encoding) as f:
        return f.read()


def write_file(
    path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
) -> None:
    """
    写入文件

    Args:
        path: 文件路径
        content: 文件内容
        encoding: 编码格式
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding=encoding) as f:
        f.write(content)


def compress_html(html: str) -> str:
    """压缩 HTML（去除注释、多余空格）"""
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    html = re.sub(r"\s+", " ", html)
    html = re.sub(r">\s+<", "><", html)
    return html.strip()
