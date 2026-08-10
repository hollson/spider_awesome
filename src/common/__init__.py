"""公共层模块"""
from src.common.logger import logger, setup_logger
from src.common.http_client import HttpClient, create_client
from src.common.utils import generate_id, parse_datetime, cost_minutes, ensure_dir
from src.common.html import compress_html, HtmlProcessor
from src.common.time_utils import parse_datetime as parse_dt, cost_minutes as calc_minutes
from src.common.exceptions import (
    DataCollectorError,
    CollectorError,
    RequestError,
    ParseError,
    ProcessorError,
    ValidationError,
    StorageError,
    DatabaseError,
    SchedulerError,
)

__all__ = [
    "logger",
    "setup_logger",
    "HttpClient",
    "create_client",
    "generate_id",
    "parse_datetime",
    "cost_minutes",
    "ensure_dir",
    "compress_html",
    "HtmlProcessor",
    "DataCollectorError",
    "CollectorError",
    "RequestError",
    "ParseError",
    "ProcessorError",
    "ValidationError",
    "StorageError",
    "DatabaseError",
    "SchedulerError",
]
