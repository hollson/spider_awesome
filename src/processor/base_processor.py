"""
处理层抽象基类
定义数据清洗、转换、校验的统一接口
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseProcessor(ABC):
    """
    处理器抽象基类

    所有处理器必须继承此类并实现 process 方法
    """

    @abstractmethod
    def process(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        处理数据

        Args:
            records: 待处理的数据列表

        Returns:
            处理后的数据列表
        """
        raise NotImplementedError
