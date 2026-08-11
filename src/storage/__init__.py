"""存储层模块"""

from src.storage.base_storage import BaseStorage
from src.storage.mysql_store import MySQLStorage

__all__ = ["BaseStorage", "MySQLStorage"]
