"""
通用工具函数
时间转换、MD5 生成、文件操作等
"""

import hashlib
import json
from pathlib import Path
from typing import Any

from src.common.html import compress_html  # noqa: F401
from src.common.time_utils import cost_minutes, parse_datetime  # noqa: F401


def generate_id(*fields: Any) -> str:
    """
    根据字段组合生成唯一 ID（MD5）

    Args:
        *fields: 用于生成 ID 的字段

    Returns:
        MD5 哈希值
    """
    data = json.dumps(fields, sort_keys=True, default=str)
    return hashlib.md5(data.encode(), usedforsecurity=False).hexdigest()


def ensure_dir(path: str | Path) -> Path:
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


def read_file(path: str | Path, encoding: str = "utf-8") -> str:
    """
    读取文件内容

    Args:
        path: 文件路径
        encoding: 编码格式

    Returns:
        文件内容
    """
    with open(path, encoding=encoding) as f:
        return f.read()


def write_file(
    path: str | Path,
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
