"""
文本清洗工具
去除空白、提取数字、截断文本等
"""

import re


def clean_text(text: str | None, extra_chars: str = "") -> str:
    """
    清洗文本：去除首尾空白、合并连续空格、移除不可见字符

    Args:
        text: 原始文本
        extra_chars: 额外需要移除的字符

    Returns:
        清洗后的文本
    """
    if not text:
        return ""
    # 移除不可见字符（保留换行和制表符）
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # 合并连续空白为单个空格
    text = re.sub(r"[^\S\n]+", " ", text)
    # 移除指定字符
    if extra_chars:
        for ch in extra_chars:
            text = text.replace(ch, "")
    return text.strip()


def extract_numbers(text: str | None) -> list[float]:
    """
    从文本中提取所有数字（支持整数和小数）

    Args:
        text: 原始文本

    Returns:
        数字列表
    """
    if not text:
        return []
    matches = re.findall(r"-?\d+\.?\d*", text)
    return [float(m) for m in matches]


def extract_ints(text: str | None) -> list[int]:
    """
    从文本中提取所有整数

    Args:
        text: 原始文本

    Returns:
        整数列表
    """
    if not text:
        return []
    matches = re.findall(r"-?\d+", text)
    return [int(m) for m in matches]


def truncate_text(text: str | None, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本到指定长度

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后添加的后缀

    Returns:
        截断后的文本
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def remove_html_tags(html: str | None) -> str:
    """
    移除 HTML 标签，保留纯文本

    Args:
        html: HTML 字符串

    Returns:
        纯文本
    """
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", "", html)
    return clean_text(text)


def extract_between(
    text: str | None,
    start: str,
    end: str,
) -> str | None:
    """
    提取两个标记之间的文本

    Args:
        text: 原始文本
        start: 起始标记
        end: 结束标记

    Returns:
        提取的文本，未找到返回 None
    """
    if not text:
        return None
    pattern = re.escape(start) + r"(.*?)" + re.escape(end)
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1) if match else None
