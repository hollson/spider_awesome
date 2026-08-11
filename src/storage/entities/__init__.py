"""
数据表实体模块
按表拆分为独立文件，便于维护

使用方式：
    from src.storage.entities import Base, BaseRecord, DataRecord, CollectorTask, CollectLog
"""

from src.storage.entities.base import Base
from src.storage.entities.base_record import BaseRecord
from src.storage.entities.collect_log import CollectLog
from src.storage.entities.collector_task import CollectorTask
from src.storage.entities.data_record import DataRecord

__all__ = [
    "Base",
    "BaseRecord",
    "DataRecord",
    "CollectorTask",
    "CollectLog",
]
