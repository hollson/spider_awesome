"""
自定义异常类
统一管理项目中的异常类型
"""
from typing import Any


class DataCollectorError(Exception):
    """基础异常类"""
    pass


class CollectorError(DataCollectorError):
    """采集异常"""
    pass


class RequestError(CollectorError):
    """请求异常"""
    def __init__(self, url: str, message: str = "请求失败", status_code: int = None):
        self.url = url
        self.status_code = status_code
        super().__init__(f"{message}: {url} (status={status_code})")


class ParseError(CollectorError):
    """解析异常"""
    def __init__(self, source: str, message: str = "数据解析失败"):
        self.source = source
        super().__init__(f"{message}: {source}")


class ProcessorError(DataCollectorError):
    """处理异常"""
    pass


class ValidationError(ProcessorError):
    """校验异常"""
    def __init__(self, field: str, value: Any, message: str = "数据校验失败"):
        self.field = field
        self.value = value
        super().__init__(f"{message}: {field}={value}")


class StorageError(DataCollectorError):
    """存储异常"""
    pass


class DatabaseError(StorageError):
    """数据库异常"""
    pass


class SchedulerError(DataCollectorError):
    """调度异常"""
    pass
