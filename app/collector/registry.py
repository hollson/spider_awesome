"""
采集器注册表
自动发现 + 配置驱动，支持动态启停

配置来源：source_define.py（代码即配置）
配置覆盖：ENV 环境变量 COLLECTOR_{NAME}_{FIELD}
"""

import importlib
import os
from pathlib import Path

from app.collector.base_collector import BaseCollector
from app.collector.source_define import SOURCES, SourceMeta
from app.common.logger import logger

# 采集器缓存
_collectors_cache: dict[str, type[BaseCollector]] | None = None


def _discover_collectors() -> dict[str, type[BaseCollector]]:
    """
    自动扫描 source_*.py，发现采集器

    约定：
    - 文件名：source_resolve_{name}.py 或 source_{name}.py
    - 类名：任意（继承 BaseCollector 即可）
    - name 从类的 name 属性获取

    注意：跳过 source_define.py（定义文件，不是采集器）
    """
    collectors = {}
    collector_dir = Path(__file__).parent

    for file_path in collector_dir.glob("source_*.py"):
        stem = file_path.stem
        if stem == "source_define":
            continue  # 跳过定义文件

        try:
            module = importlib.import_module(f"app.collector.{stem}")

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseCollector) and attr is not BaseCollector:
                    # 临时实例化以获取 name 属性
                    temp_instance = attr()
                    name = temp_instance.name
                    collectors[name] = attr
                    logger.trace(f"[Registry] 发现采集器: {name} -> {attr.__name__}")
                    break
        except Exception as e:
            logger.warning(f"[Registry] 加载采集器 {stem} 失败: {e}")

    return collectors


def _load_collector_config() -> dict:
    """
    加载采集器配置

    优先级：ENV > source_define.py 默认值
    """
    config = {}

    # 1. 从 source_define.py 加载默认值
    for name, meta in SOURCES.items():
        config[name] = {
            "enabled": meta.enabled,
            "cron": meta.cron,
            "timeout": meta.timeout,
            "retry": meta.retry,
            "retry_delay": meta.retry_delay,
            "persist": meta.persist,
        }

    # 2. ENV 覆盖（最高优先级）
    # COLLECTOR_EXAMPLE_ALERION_ENABLED=true → example_alerion.enabled
    for key, value in os.environ.items():
        if key.startswith("COLLECTOR_"):
            parts = key.replace("COLLECTOR_", "").lower().split("_", 1)
            if len(parts) == 2:
                collector_name, field = parts
                if collector_name not in config:
                    config[collector_name] = {}
                # 类型转换
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                elif value.isdigit():
                    value = int(value)
                config[collector_name][field] = value

    return config


def get_collector_config() -> dict:
    """获取采集器配置"""
    return _load_collector_config()


def get_enabled_collectors() -> list[str]:
    """获取已启用的采集器名称列表"""
    config = _load_collector_config()

    enabled = []
    for name, cfg in config.items():
        if cfg.get("enabled", True):
            enabled.append(name)

    return enabled


def get_collector_schedule(name: str) -> dict:
    """
    获取指定采集器的调度配置

    Returns:
        {"cron": "0 */2 * * *", "timeout": 300, "retry": 3, ...}
    """
    config = _load_collector_config()
    collector_config = config.get(name, {})

    # 合并默认值
    schedule = {
        "cron": "0 */1 * * *",
        "timeout": 300,
        "retry": 3,
        "retry_delay": 60,
    }
    schedule.update(collector_config)

    return schedule


def get_source_meta(name: str) -> SourceMeta:
    """获取指定数据源元信息"""
    from app.collector.source_define import get_source

    return get_source(name)


def get_collectors() -> dict[str, type[BaseCollector]]:
    """获取所有采集器类（自动发现）"""
    global _collectors_cache
    if _collectors_cache is None:
        _collectors_cache = _discover_collectors()
    return _collectors_cache


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
    collectors = get_collectors()
    collector_cls = collectors.get(name.lower())
    if not collector_cls:
        available = ", ".join(collectors.keys())
        raise ValueError(f"Unknown collector: {name}. Available: {available}")
    return collector_cls()


def list_collectors() -> list[str]:
    """列出所有可用的采集器名称"""
    return list(get_collectors().keys())


def list_enabled_collectors() -> list[str]:
    """列出已启用的采集器名称"""
    enabled_config = get_enabled_collectors()
    all_collectors = list_collectors()

    # 只返回配置中启用且实际存在的采集器
    return [name for name in enabled_config if name in all_collectors]


def get_all_collectors() -> list[BaseCollector]:
    """获取所有采集器实例"""
    return [cls() for cls in get_collectors().values()]


def reload_collectors():
    """重新加载采集器（清空缓存）"""
    global _collectors_cache
    _collectors_cache = None
    logger.info("[Registry] 采集器已重新加载")
