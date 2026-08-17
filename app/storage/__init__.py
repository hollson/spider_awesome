"""存储层模块"""

from app.storage.base_storage import BaseStorage
from app.storage.store import DataStorage

__all__ = ["BaseStorage", "DataStorage"]
