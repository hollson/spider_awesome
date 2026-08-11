"""
SQLAlchemy ORM 数据模型（聚合导出）

实体已拆分到 storage/entities/ 目录下：
- entities/base.py          → Base 声明
- entities/base_record.py   → BaseRecord（通用表）
- entities/data_record.py   → DataRecord（航空业务表）
- entities/collector_task.py → CollectorTask（任务记录表）
- entities/collect_log.py   → CollectLog（审计日志表）

本文件保留向后兼容，新代码请直接从 entities 导入
"""

from src.storage.entities import (  # noqa: F401
    Base,
    BaseRecord,
    CollectLog,
    CollectorTask,
    DataRecord,
)

__all__ = [
    "Base",
    "BaseRecord",
    "DataRecord",
    "CollectorTask",
    "CollectLog",
]
