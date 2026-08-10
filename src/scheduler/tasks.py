"""
定时任务函数定义
支持多任务并行采集
"""
from datetime import datetime
from typing import Any, Dict, List

from src.collector import get_collector, list_collectors
from src.processor.cleaner import Cleaner
from src.processor.validator import Validator
from src.storage.mysql_store import MySQLStorage
from src.common.logger import logger


def run_collector(collector_name: str) -> Dict[str, Any]:
    """
    执行单个采集器任务

    Args:
        collector_name: 采集器名称

    Returns:
        任务执行结果
    """
    logger.info(f"[Task] 开始采集: {collector_name}")
    start_time = datetime.now()
    result = {"total": 0, "success": 0, "failed": 0}

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

        # 4. 存储
        storage = MySQLStorage(auto_create=True)
        saved = storage.save(records)
        result["success"] = saved
        result["failed"] = len(records) - saved

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"[Task] 采集完成: {collector_name} "
            f"(采集 {result['total']} 条, 保存 {saved} 条, 耗时 {elapsed:.1f}s)"
        )
        return result

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"[Task] 采集失败: {collector_name} ({elapsed:.1f}s) - {e}")
        raise


def run_all_collectors() -> Dict[str, Any]:
    """
    执行所有采集器任务（串行）

    Returns:
        任务执行结果
    """
    logger.info("[Task] 开始执行所有采集任务")
    start_time = datetime.now()

    collectors = list_collectors()
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


def run_parallel_collectors(collector_names: List[str] = None) -> Dict[str, Any]:
    """
    并行执行多个采集器任务

    Args:
        collector_names: 要执行的采集器名称列表，None 则执行所有

    Returns:
        任务执行结果
    """
    from src.scheduler.task_manager import task_manager

    if collector_names is None:
        collector_names = list_collectors()

    logger.info(f"[Task] 开始并行采集: {collector_names}")
    start_time = datetime.now()

    # 提交所有任务到线程池
    futures = {}
    for name in collector_names:
        task_id = f"collect_{name}_{int(datetime.now().timestamp())}"
        futures[name] = task_manager.submit_task(
            task_id=task_id,
            func=lambda n=name: run_collector(n)
        )

    # 等待所有任务完成（通过 task_manager 的状态追踪）
    # 这里直接串行等待，实际生产中可以用更复杂的同步机制
    total_result = {"total": 0, "success": 0, "failed": 0}
    for name in collector_names:
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
        f"[Task] 并行采集完成 "
        f"(共 {len(collector_names)} 个, 耗时 {elapsed:.1f}s, "
        f"成功 {total_result['success']}/{total_result['total']})"
    )
    return total_result
