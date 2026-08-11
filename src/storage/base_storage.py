"""
存储层抽象基类
定义数据持久化存储的统一接口
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseStorage(ABC):
    """
    存储抽象基类

    所有存储实现必须继承此类
    """

    @abstractmethod
    def save(self, records: list[dict[str, Any]]) -> int:
        """
        保存数据

        Args:
            records: 待保存的数据列表

        Returns:
            成功保存的数量
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self, record_id: str) -> bool:
        """
        检查数据是否存在

        Args:
            record_id: 数据 ID

        Returns:
            是否存在
        """
        raise NotImplementedError

    @abstractmethod
    def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        统计数据数量

        Args:
            filters: 过滤条件

        Returns:
            数据数量
        """
        raise NotImplementedError

    def save_one(self, record: dict[str, Any]) -> bool:
        """
        保存单条数据

        Args:
            record: 待保存的数据

        Returns:
            是否成功
        """
        results = self.save([record])
        return results > 0
