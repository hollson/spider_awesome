"""
时间处理工具模块
支持多种日期时间格式的解析和转换
"""
import re
from datetime import date, datetime
from typing import Optional, Union


# 月份映射
MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# 支持的日期格式
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
    "%d %b, %Y",
    "%d %B, %Y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d %Y",
    "%B %d %Y",
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
    "%m/%d/%y %I:%M:%S %p",
    "%d-%m-%Y %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%Y.%m.%d %H:%M:%S",
    "%a, %d %b %Y %H:%M:%S %z",
]


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
            return datetime.strptime(value, fmt)
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


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间

    Args:
        dt: datetime 对象
        fmt: 格式字符串

    Returns:
        格式化后的字符串
    """
    if dt is None:
        return ""
    return dt.strftime(fmt)


def convert_around(month_day: str) -> Optional[str]:
    """
    将 "December 31" 格式的日期补充年份

    Args:
        month_day: 月日字符串

    Returns:
        带年份的日期字符串
    """
    try:
        now = datetime.now()
        current_year = now.year
        current_month = now.month

        parts = month_day.strip().split()
        if len(parts) != 2:
            return None

        month_name, day_str = parts
        month = MONTH_MAP.get(month_name.lower())
        if month is None:
            return None

        day = int(day_str)

        # 计算月份差
        diff = (current_month - month + 12) % 12
        year = current_year + 1 if diff > 6 else current_year

        return date(year, month, day).isoformat()
    except Exception:
        return None
