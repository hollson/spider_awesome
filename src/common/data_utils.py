"""
数据处理工具
嵌套字典访问、去重、分批等
"""

from typing import Any


def safe_get(data: dict, key_path: str, default: Any = None) -> Any:
    """
    安全获取嵌套字典值

    支持点号分隔的路径，如 "a.b.c"

    Args:
        data: 字典数据
        key_path: 键路径（点号分隔）
        default: 默认值

    Returns:
        对应值或默认值

    Examples:
        >>> safe_get({"a": {"b": {"c": 1}}}, "a.b.c")
        1
        >>> safe_get({"a": {"b": {"c": 1}}}, "a.b.d", "missing")
        'missing'
    """
    if not data or not key_path:
        return default

    keys = key_path.split(".")
    current = data

    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, (list, tuple)) and key.isdigit():
            idx = int(key)
            current = current[idx] if 0 <= idx < len(current) else None
        else:
            return default

        if current is None:
            return default

    return current


def deduplicate(
    records: list[dict],
    key: str = "id",
    keep: str = "first",
) -> list[dict]:
    """
    列表去重（基于指定键）

    Args:
        records: 字典列表
        key: 去重依据的键名
        keep: 保留策略 - "first" 保留首个, "last" 保留最后

    Returns:
        去重后的列表
    """
    if keep == "last":
        records = list(reversed(records))

    seen = set()
    result = []
    for record in records:
        value = record.get(key)
        if value not in seen:
            seen.add(value)
            result.append(record)

    if keep == "last":
        result.reverse()

    return result


def chunk_list(items: list, size: int = 100) -> list[list]:
    """
    将列表拆分为固定大小的批次

    Args:
        items: 原始列表
        size: 每批大小

    Returns:
        分批后的列表
    """
    return [items[i : i + size] for i in range(0, len(items), size)]


def merge_dicts(*dicts: dict, deep: bool = True) -> dict:
    """
    合并多个字典

    Args:
        dicts: 要合并的字典
        deep: 是否深度合并

    Returns:
        合并后的字典
    """
    if not dicts:
        return {}

    result = {}
    for d in dicts:
        if not d:
            continue
        if deep:
            for key, value in d.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value, deep=True)
                else:
                    result[key] = value
        else:
            result.update(d)

    return result


def filter_none(data: dict) -> dict:
    """
    移除字典中的 None 值

    Args:
        data: 原始字典

    Returns:
        过滤后的字典
    """
    return {k: v for k, v in data.items() if v is not None}


def flatten_dict(data: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
    展平嵌套字典

    Args:
        data: 嵌套字典
        parent_key: 父键名
        sep: 键分隔符

    Returns:
        展平后的字典

    Examples:
        >>> flatten_dict({"a": {"b": 1, "c": 2}})
        {"a.b": 1, "a.c": 2}
    """
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
