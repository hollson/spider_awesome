"""
通用工具函数
统一入口，按需导入各子模块
"""

import hashlib
import json
from pathlib import Path
from typing import Any

# 类型转换
from src.common.convert_utils import (  # noqa: F401
    format_price,
    safe_json,
    to_bool,
    to_float,
    to_int,
)

# 数据处理
from src.common.data_utils import (  # noqa: F401
    chunk_list,
    deduplicate,
    filter_none,
    flatten_dict,
    merge_dicts,
    safe_get,
)

# 文件操作
from src.common.file_utils import (  # noqa: F401
    file_hash,
    load_json,
    load_jsonl,
    safe_filename,
    save_csv,
    save_json,
)
from src.common.html import compress_html  # noqa: F401

# 文本清洗
from src.common.text_utils import (  # noqa: F401
    clean_text,
    extract_between,
    extract_ints,
    extract_numbers,
    remove_html_tags,
    truncate_text,
)
from src.common.time_utils import cost_minutes, parse_datetime  # noqa: F401

# URL 处理
from src.common.url_utils import (  # noqa: F401
    decode_url,
    encode_url,
    extract_domain,
    extract_query_params,
    is_same_domain,
    is_valid_url,
    join_url,
    normalize_url,
)


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
