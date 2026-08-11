"""
采集器注册表
自动发现 + 配置驱动，支持动态启停
"""

import importlib
from pathlib import Path

import yaml

from src.collector.base_collector import BaseCollector
from src.common.logger import logger

# 采集器缓存
_collectors_cache: dict[str, type[BaseCollector]] | None = None


def _discover_collectors() -> dict[str, type[BaseCollector]]:
    """
    自动扫描 source_*.py，发现采集器

    约定：
    - 文件名：source_{name}.py
    - 类名：任意（继承 BaseCollector 即可）
    - name 为去掉 source_ 前缀后的部分（如 source_example_alerion → example_alerion）
    """
    collectors = {}
    collector_dir = Path(__file__).parent

    for file_path in collector_dir.glob("source_*.py"):
        stem = file_path.stem
        name = stem.replace("source_", "")

        try:
            module = importlib.import_module(f"src.collector.{stem}")

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BaseCollector) and attr is not BaseCollector:
                    collectors[name] = attr
                    logger.debug(f"[Registry] 发现采集器: {name} -> {attr.__name__}")
                    break
        except Exception as e:
            logger.warning(f"[Registry] 加载采集器 {name} 失败: {e}")

    return collectors


def _load_collector_config() -> dict:
    """
    加载采集器配置（YAML + ENV 覆盖）

    优先级：ENV > collectors.local.yml > collectors.yml
    """
    import os

    configs_dir = Path(__file__).parent.parent.parent / "configs"
    config = {"scheduler": {}, "collectors": {}}

    # 1. 加载 collectors.yml
    base_config_file = configs_dir / "collectors.yml"
    if base_config_file.exists():
        with open(base_config_file, encoding="utf-8") as f:
            base_config = yaml.safe_load(f) or {}
            config["scheduler"] = base_config.get("scheduler", {})
            config["collectors"] = base_config.get("collectors", {})

    # 2. 加载 collectors.local.yml（覆盖）
    local_config_file = configs_dir / "collectors.local.yml"
    if local_config_file.exists():
        with open(local_config_file, encoding="utf-8") as f:
            local_config = yaml.safe_load(f) or {}
            if "scheduler" in local_config:
                config["scheduler"].update(local_config["scheduler"])
            if "collectors" in local_config:
                config["collectors"].update(local_config["collectors"])

    # 3. ENV 覆盖（最高优先级）
    for key, value in os.environ.items():
        if key.startswith("COLLECTOR_"):
            # COLLECTOR_ALERION_ENABLED=true → collectors.alerion.enabled
            parts = key.replace("COLLECTOR_", "").lower().split("_", 1)
            if len(parts) == 2:
                name, field = parts
                if name not in config["collectors"]:
                    config["collectors"][name] = {}
                # 类型转换
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                elif value.isdigit():
                    value = int(value)
                config["collectors"][name][field] = value

    return config


def get_collector_config() -> dict:
    """获取采集器配置"""
    return _load_collector_config()


def get_enabled_collectors() -> list[str]:
    """获取已启用的采集器名称列表"""
    config = _load_collector_config()
    collectors_config = config.get("collectors", {})

    enabled = []
    for name, cfg in collectors_config.items():
        if cfg.get("enabled", True):  # 默认启用
            enabled.append(name)

    return enabled


def get_collector_schedule(name: str) -> dict:
    """
    获取指定采集器的调度配置

    Returns:
        {"cron": "0 */2 * * *", "timeout": 300, "retry": 3, ...}
    """
    config = _load_collector_config()
    scheduler_defaults = config.get("scheduler", {})
    collector_config = config.get("collectors", {}).get(name, {})

    # 合并：采集器配置 > 调度器默认值
    schedule = {
        "cron": scheduler_defaults.get("default_cron", "0 0 * * *"),
        "timeout": scheduler_defaults.get("timeout", 300),
        "retry": scheduler_defaults.get("retry", 3),
        "retry_delay": scheduler_defaults.get("retry_delay", 60),
    }
    schedule.update(collector_config)

    return schedule


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
