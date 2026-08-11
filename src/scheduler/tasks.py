"""
定时任务函数定义
支持多任务并行采集，按采集器独立调度
"""

from datetime import datetime
from typing import Any

from src.collector import get_collector, list_enabled_collectors
from src.common.logger import logger
from src.processor.cleaner import Cleaner
from src.processor.validator import Validator
from src.storage.mysql_store import MySQLStorage


def run_collector(collector_name: str) -> dict[str, Any]:
    """
    执行单个采集器任务

    Args:
        collector_name: 采集器名称

    Returns:
        任务执行结果
    """
    from src.collector.registry import get_collector_schedule

    logger.info(f"[Task] 开始采集: {collector_name}")
    start_time = datetime.now()
    result = {"total": 0, "success": 0, "failed": 0}

    # 获取采集器配置
    schedule = get_collector_schedule(collector_name)
    persist = schedule.get("persist", True)  # 默认持久化

    try:
        # 1. 采集
        collector = get_collector(collector_name)
        records = collector.fetch()
        result["total"] = len(records)

        # 2. 清洗
        cleaner = Cleaner()
        records = cleaner.process(records)

        # 3. 校验
        validator = Validator()
        records = validator.process(records)

        # 4. 存储（根据配置决定是否入库）
        if persist:
            storage = MySQLStorage(auto_create=True)
            saved = storage.save(records)
            result["success"] = saved
            result["failed"] = len(records) - saved
        else:
            # 不入库，只统计通过校验的数量
            result["success"] = len(records)
            result["failed"] = 0
            logger.info(f"[Task] {collector_name} 不入库模式，跳过存储")

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"[Task] 采集完成: {collector_name} (采集 {result['total']} 条, "
            f"{'保存' if persist else '处理'} {result['success']} 条, 耗时 {elapsed:.1f}s)"
        )
        return result

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"[Task] 采集失败: {collector_name} ({elapsed:.1f}s) - {e}")
        raise


def run_all_collectors() -> dict[str, Any]:
    """
    执行所有已启用的采集器任务（串行）

    Returns:
        任务执行结果
    """
    logger.info("[Task] 开始执行所有采集任务")
    start_time = datetime.now()

    collectors = list_enabled_collectors()
    total_result = {"total": 0, "success": 0, "failed": 0}

    for name in collectors:
        try:
            result = run_collector(name)
            total_result["total"] += result["total"]
            total_result["success"] += result["success"]
            total_result["failed"] += result["failed"]
        except Exception as e:
            logger.error(f"[Task] {name} 执行失败: {e}")
            continue

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"[Task] 所有采集任务完成 "
        f"(共 {len(collectors)} 个, 耗时 {elapsed:.1f}s, "
        f"成功 {total_result['success']}/{total_result['total']})"
    )
    return total_result


def run_parallel_collectors(collector_names: list[str] = None) -> dict[str, Any]:
    """
    并行执行多个采集器任务

    Args:
        collector_names: 要执行的采集器名称列表，None 则执行所有已启用的

    Returns:
        任务执行结果
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from src.settings import settings

    if collector_names is None:
        collector_names = list_enabled_collectors()

    logger.info(f"[Task] 开始并行采集: {collector_names}")
    start_time = datetime.now()

    total_result = {"total": 0, "success": 0, "failed": 0}

    with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
        futures = {executor.submit(run_collector, name): name for name in collector_names}
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                total_result["total"] += result["total"]
                total_result["success"] += result["success"]
                total_result["failed"] += result["failed"]
            except Exception as e:
                logger.error(f"[Task] {name} 执行失败: {e}")

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"[Task] 并行采集完成 "
        f"(共 {len(collector_names)} 个, 耗时 {elapsed:.1f}s, "
        f"成功 {total_result['success']}/{total_result['total']})"
    )
    return total_result


def parse_cron_to_hour_minute(cron: str) -> tuple[int, int]:
    """
    简单解析 cron 表达式，提取小时和分钟

    支持格式：
    - "0 0 * * *" → (0, 0)
    - "30 */2 * * *" → (None, 30)  # 每2小时的30分
    - "0 */6 * * *" → (None, 0)    # 每6小时

    Returns:
        (hour, minute) 元组，None 表示不固定
    """
    parts = cron.strip().split()
    if len(parts) < 5:
        return 0, 0

    minute_str, hour_str = parts[0], parts[1]

    # 解析分钟
    if minute_str.startswith("*/"):
        minute = 0  # 间隔执行，从0分开始
    else:
        minute = int(minute_str)

    # 解析小时
    if hour_str.startswith("*/"):
        hour = 0  # 间隔执行，从0时开始
    else:
        hour = int(hour_str)

    return hour, minute
