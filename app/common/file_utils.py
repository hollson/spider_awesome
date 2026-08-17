"""
文件操作工具
JSON/CSV 读写、安全文件名生成等
"""

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def save_json(
    file_path: str | Path,
    data: Any,
    indent: int = 2,
    ensure_ascii: bool = False,
    mode: str = "w",
) -> str:
    """
    保存数据为 JSON 文件

    Args:
        file_path: 文件路径
        data: 要保存的数据
        indent: 缩进空格数
        ensure_ascii: 是否转义非 ASCII 字符
        mode: 写入模式 - "w" 覆盖, "a" 追加

    Returns:
        保存的文件路径
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, mode, encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        if mode == "a":
            f.write("\n")

    return str(path)


def load_json(
    file_path: str | Path,
    default: Any = None,
    encoding: str = "utf-8",
) -> Any:
    """
    加载 JSON 文件

    Args:
        file_path: 文件路径
        default: 文件不存在或解析失败时的默认值
        encoding: 文件编码

    Returns:
        解析后的数据
    """
    path = Path(file_path)
    if not path.exists():
        return default if default is not None else {}

    try:
        with open(path, encoding=encoding) as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return default if default is not None else {}


def load_jsonl(
    file_path: str | Path,
    encoding: str = "utf-8",
) -> list[dict]:
    """
    加载 JSONL 文件（每行一个 JSON）

    Args:
        file_path: 文件路径
        encoding: 文件编码

    Returns:
        数据列表
    """
    path = Path(file_path)
    if not path.exists():
        return []

    results = []
    with open(path, encoding=encoding) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return results


def save_csv(
    file_path: str | Path,
    data: list[dict],
    fieldnames: list[str] | None = None,
    mode: str = "w",
) -> str:
    """
    保存数据为 CSV 文件

    Args:
        file_path: 文件路径
        data: 字典列表
        fieldnames: 列名列表（None 则从数据推断）
        mode: 写入模式

    Returns:
        保存的文件路径
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        return str(path)

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(path, mode, newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if mode == "w":
            writer.writeheader()
        writer.writerows(data)

    return str(path)


def safe_filename(name: str, max_length: int = 200) -> str:
    """
    生成安全的文件名（移除非法字符）

    Args:
        name: 原始文件名
        max_length: 最大长度

    Returns:
        安全的文件名
    """
    # 移除非法字符
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    # 合并连续下划线
    safe = re.sub(r"_+", "_", safe)
    # 截断
    return safe[:max_length]


def file_hash(file_path: str | Path, algorithm: str = "md5") -> str:
    """
    计算文件哈希值（可用于缓存判断）

    Args:
        file_path: 文件路径
        algorithm: 哈希算法

    Returns:
        十六进制哈希字符串
    """
    h = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(dir_path: str | Path) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        dir_path: 目录路径

    Returns:
        目录 Path 对象
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path
