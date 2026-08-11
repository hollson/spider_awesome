"""
类型转换工具
安全的 int/float/JSON 转换，处理各种异常输入
"""

import json
import re
from typing import Any


def to_int(value: Any, default: int = 0) -> int:
    """
    安全转换为整数

    Args:
        value: 原始值
        default: 转换失败时的默认值

    Returns:
        整数值
    """
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        # 去除逗号等千位分隔符
        cleaned = value.replace(",", "").strip()
        # 提取第一个整数
        match = re.search(r"-?\d+", cleaned)
        if match:
            return int(match.group())
    return default


def to_float(value: Any, default: float = 0.0) -> float:
    """
    安全转换为浮点数

    Args:
        value: 原始值
        default: 转换失败时的默认值

    Returns:
        浮点数值
    """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "").strip()
        match = re.search(r"-?\d+\.?\d*", cleaned)
        if match:
            return float(match.group())
    return default


def safe_json(
    text: str | None,
    default: Any = None,
) -> Any:
    """
    安全解析 JSON

    Args:
        text: JSON 字符串
        default: 解析失败时的默认值

    Returns:
        解析后的对象
    """
    if not text:
        return default
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def to_bool(value: Any, default: bool = False) -> bool:
    """
    安全转换为布尔值

    支持: true/false, 1/0, yes/no, on/off

    Args:
        value: 原始值
        default: 转换失败时的默认值

    Returns:
        布尔值
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.lower().strip() in ("true", "1", "yes", "on")
    return default


def format_price(
    value: Any,
    currency: str = "",
    decimals: int = 2,
) -> str:
    """
    格式化价格显示

    Args:
        value: 价格值
        currency: 货币符号
        decimals: 小数位数

    Returns:
        格式化后的价格字符串
    """
    price = to_float(value, 0.0)
    formatted = f"{price:,.{decimals}f}"
    if currency:
        return f"{currency}{formatted}"
    return formatted
