"""
数据表实体模块
按表拆分为独立文件，便于维护

使用方式：
    from app.storage.entities import Base, BaseRecord, DataRecord, CollectorTask, CollectLog
"""

from app.storage.entities.base import Base
from app.storage.entities.base_record import BaseRecord
from app.storage.entities.collect_log import CollectLog
from app.storage.entities.collector_task import CollectorTask
from app.storage.entities.data_record import DataRecord

__all__ = [
    "Base",
    "BaseRecord",
    "DataRecord",
    "CollectorTask",
    "CollectLog",
]
