"""
定时任务函数定义
定义所有采集任务的具体执行逻辑
"""
from typing import List, Dict, Any

from src.collector import get_collector, list_collectors
from src.processor.cleaner import Cleaner
from src.processor.validator import Validator
from src.storage.mysql_store import MySQLStorage
from src.common.logger import logger


def run_collector(collector_name: str):
    """
    执行单个采集器任务

    Args:
        collector_name: 采集器名称
    """
    logger.info(f"[Task] 开始执行采集: {collector_name}")
    start_time = datetime.now()

    try:
        # 1. 采集
        collector = get_collector(collector_name)
        records = collector.fetch()

        # 2. 清洗
        cleaner = Cleaner()
        records = cleaner.process(records)

        # 3. 校验
        validator = Validator()
        records = validator.process(records)

        # 4. 存储
        storage = MySQLStorage(auto_create=True)
        saved_count = storage.save(records)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"[Task] 采集完成: {collector_name} "
            f"(采集 {len(records)} 条, 保存 {saved_count} 条, 耗时 {elapsed:.1f}s)"
        )
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"[Task] 采集失败: {collector_name} ({elapsed:.1f}s) - {e}")


def run_all_collectors():
    """执行所有启用的采集器任务"""
    logger.info("[Task] 开始执行所有采集任务")
    start_time = datetime.now()

    collectors = list_collectors()
    for name in collectors:
        run_collector(name)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"[Task] 所有采集任务完成 (共 {len(collectors)} 个, 耗时 {elapsed:.1f}s)")


# 需要导入 datetime
from datetime import datetime
