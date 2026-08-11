"""
采集器注册表
统一管理所有可用的采集器
"""

from src.collector.base_collector import BaseCollector
from src.collector.source_alerion import AlerionCollector
from src.collector.source_asl import ASLCollector
from src.collector.source_noble import NobleCollector

# 采集器注册表
COLLECTORS: dict[str, type[BaseCollector]] = {
    "alerion": AlerionCollector,
    "asl": ASLCollector,
    "noble": NobleCollector,
}


def get_collector(name: str) -> BaseCollector:
    """
    根据名称获取采集器实例

    Args:
        name: 采集器名称

    Returns:
        采集器实例

    Raises:
        ValueError: 采集器不存在
    """
    collector_cls = COLLECTORS.get(name.lower())
    if not collector_cls:
        available = ", ".join(COLLECTORS.keys())
        raise ValueError(f"Unknown collector: {name}. Available: {available}")
    return collector_cls()


def list_collectors() -> list[str]:
    """列出所有可用的采集器名称"""
    return list(COLLECTORS.keys())


def get_all_collectors() -> list[BaseCollector]:
    """获取所有采集器实例"""
    return [cls() for cls in COLLECTORS.values()]
