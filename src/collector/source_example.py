"""
模拟采集器：用于测试并行任务执行
通过 sleep 模拟耗时的网络请求
"""
import time
from typing import Any, Dict, List

from src.collector.base_collector import BaseCollector
from src.common.logger import logger


class ExampleSlowCollector(BaseCollector):
    """慢速采集器（模拟 2s 延迟）"""

    SLEEP_SECONDS = 2

    @property
    def name(self) -> str:
        return "example_slow"

    def fetch(self) -> List[Dict[str, Any]]:
        logger.info(f"[{self.name}] 开始采集，模拟 {self.SLEEP_SECONDS}s 延迟...")
        time.sleep(self.SLEEP_SECONDS)
        logger.info(f"[{self.name}] 采集完成")
        return [
            {"id": "slow_1", "source": self.name, "collector_name": self.name, "title": "慢速数据1"},
            {"id": "slow_2", "source": self.name, "collector_name": self.name, "title": "慢速数据2"},
        ]


class ExampleMediumCollector(BaseCollector):
    """中速采集器（模拟 1s 延迟）"""

    SLEEP_SECONDS = 1

    @property
    def name(self) -> str:
        return "example_medium"

    def fetch(self) -> List[Dict[str, Any]]:
        logger.info(f"[{self.name}] 开始采集，模拟 {self.SLEEP_SECONDS}s 延迟...")
        time.sleep(self.SLEEP_SECONDS)
        logger.info(f"[{self.name}] 采集完成")
        return [
            {"id": "medium_1", "source": self.name, "collector_name": self.name, "title": "中速数据1"},
        ]


class ExampleFastCollector(BaseCollector):
    """快速采集器（模拟 0.5s 延迟）"""

    SLEEP_SECONDS = 0.5

    @property
    def name(self) -> str:
        return "example_fast"

    def fetch(self) -> List[Dict[str, Any]]:
        logger.info(f"[{self.name}] 开始采集，模拟 {self.SLEEP_SECONDS}s 延迟...")
        time.sleep(self.SLEEP_SECONDS)
        logger.info(f"[{self.name}] 采集完成")
        return [
            {"id": "fast_1", "source": self.name, "collector_name": self.name, "title": "快速数据1"},
            {"id": "fast_2", "source": self.name, "collector_name": self.name, "title": "快速数据2"},
            {"id": "fast_3", "source": self.name, "collector_name": self.name, "title": "快速数据3"},
        ]
