"""
全局日志模块
基于 Loguru，支持控制台彩色输出 + 文件按天轮转
"""

import logging
import sys

from loguru import logger

from src.settings import settings

# 日志级别缩写
_LEVEL_ABBR = {
    "DEBUG": "DBG",
    "INFO": "INF",
    "WARNING": "WRN",
    "ERROR": "ERR",
    "CRITICAL": "CRT",
}


def setup_logger() -> None:
    """
    初始化 Loguru 日志系统

    - 控制台：彩色输出到 stderr
    - 文件：按天轮转，自动保留指定天数
    - 拦截 stdlib logging：统一汇入 Loguru
    """
    # 1) 移除 Loguru 默认 handler
    logger.remove()

    # 2) 控制台输出 — 彩色格式
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:MM-DD HH:mm:ss}</green> "
            "<level>{extra[level_abbr]}</level> "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # 3) 文件输出 — 按天轮转，保留指定天数
    if settings.LOG_FILE:
        import os

        log_dir = os.path.dirname(settings.LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        logger.add(
            settings.LOG_FILE,
            level=settings.LOG_LEVEL,
            format=("{time:YYYY-MM-DD HH:mm:ss.SSS} {extra[level_abbr]} {name}:{function}:{line} {message}"),
            rotation="00:00",  # 每天午夜轮转
            retention=f"{settings.LOG_RETENTION} days",
            encoding="utf-8",
        )

    # 4) patcher 动态注入级别缩写
    logger.configure(
        patcher=lambda record: record["extra"].update(
            level_abbr=_LEVEL_ABBR.get(record["level"].name, record["level"].name[:3])
        )
    )

    # 5) 抑制 urllib3 等第三方库的重复日志
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # 6) 拦截 stdlib logging → Loguru（只转发 WARNING 及以上）
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if record.levelno < logging.WARNING:
                return
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            frame = logging.currentframe()
            depth = 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


# 初始化日志（导入即执行）
setup_logger()


# 便捷导出，兼容原有使用方式
__all__ = ["logger", "setup_logger"]
