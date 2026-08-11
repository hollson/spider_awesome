"""
跨平台终端颜色支持

自动检测终端能力，不支持时降级为纯文本
兼容 Windows (10+)、macOS、Linux
"""

import os
import sys


def _supports_color() -> bool:
    """检测终端是否支持 ANSI 颜色"""
    # 用户明确禁用颜色
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return False

    # Windows 10+ 支持 ANSI，需先激活
    if sys.platform == "win32":
        try:
            os.system("")  # 触发 Windows 10+ ANSI 支持
        except Exception:
            return False

    # 非 TTY 输出（重定向到文件）不输出颜色
    if hasattr(sys.stdout, "isatty") and not sys.stdout.isatty():
        return False

    return True


_COLOR_ENABLED = _supports_color()


def colored(text: str, color: str) -> str:
    """
    给文本添加颜色

    Args:
        text: 要着色的文本
        color: 颜色名称 (red, green, yellow, blue, cyan, magenta, white, gray)

    Returns:
        带 ANSI 转义码的文本，不支持颜色时返回原文
    """
    if not _COLOR_ENABLED:
        return text

    colors = {
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
        "gray": "90",
    }
    code = colors.get(color, "37")
    return f"\033[{code}m{text}\033[0m"


def banner_line(char: str = "=", width: int = 50) -> str:
    """返回带颜色的分隔线"""
    return colored(char * width, "cyan")


def banner_title(text: str) -> str:
    """返回带颜色的标题文本"""
    return colored(text, "green")


def banner_label(label: str, value: str) -> str:
    """
    返回标签-值对文本，标签高亮

    Args:
        label: 标签文本（如 "环境"）
        value: 值文本（如 "dev"）

    Returns:
        格式化后的字符串，如 "  环境: \033[33mdev\033[0m"
    """
    if _COLOR_ENABLED:
        return f"  {label}: {colored(value, 'yellow')}"
    return f"  {label}: {value}"
