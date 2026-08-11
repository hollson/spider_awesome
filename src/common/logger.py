"""
全局日志模块
支持控制台 + 文件双输出，按日期自动切割
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.settings import settings


class ColorFormatter(logging.Formatter):
    """带颜色的日志格式化器（控制台使用）"""

    COLORS = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname:<8}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str = "data_collector", level: str = None, log_dir: str = None
) -> logging.Logger:
    """
    配置并返回日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别
        log_dir: 日志文件目录

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)

    # 防止重复添加 handler
    if logger.handlers:
        return logger

    level = level or settings.LOG_LEVEL
    log_dir = log_dir or settings.LOG_DIR
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 日志格式
    console_fmt = "%(asctime)s [%(levelname)s] %(message)s"
    file_fmt = "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorFormatter(console_fmt, date_fmt))
    logger.addHandler(console_handler)

    # 文件输出（按大小切割，保留 5 个备份）
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    file_handler = RotatingFileHandler(
        log_path / f"{name}_{today}.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(file_fmt, date_fmt))
    logger.addHandler(file_handler)

    return logger


# 全局日志实例
logger = setup_logger()
