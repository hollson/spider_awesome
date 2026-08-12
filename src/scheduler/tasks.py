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
from src.storage.store import DataStorage


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
        # 1. 采集（使用 safe_fetch，异常自动降级）
        collector = get_collector(collector_name)
        records = collector.safe_fetch()
        result["total"] = len(records)

        # 2. 清洗
        cleaner = Cleaner()
        records = cleaner.process(records)

        # 3. 校验
        validator = Validator()
        records = validator.process(records)

        # 4. 存储（根据配置决定是否入库）
        if persist:
            storage = DataStorage(auto_create=True)
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

        # 记录审计日志
        _save_collect_log(
            collector_name=collector_name,
            status="success",
            data_count=result["total"],
            new_count=result["success"],
            duplicate_count=result["failed"],
            duration=elapsed,
        )

        return result

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.warning(f"[Task] 采集失败: {collector_name} ({elapsed:.1f}s)")

        # 记录失败审计日志
        _save_collect_log(
            collector_name=collector_name,
            status="fail",
            data_count=0,
            duration=elapsed,
            error_msg=str(e),
        )
        raise


def _save_collect_log(
    collector_name: str,
    status: str,
    data_count: int = 0,
    new_count: int = 0,
    update_count: int = 0,
    duplicate_count: int = 0,
    duration: float = 0,
    error_msg: str = "",
):
    """保存审计日志"""
    from src.storage.models import CollectLog
    from src.storage.session import get_db_instance

    try:
        with get_db_instance().get_session() as session:
            log = CollectLog(
                collector_name=collector_name,
                status=status,
                data_count=data_count,
                new_count=new_count,
                update_count=update_count,
                duplicate_count=duplicate_count,
                duration=round(duration, 2),
                error_msg=error_msg if error_msg else None,
            )
            session.add(log)
            session.commit()
    except Exception as e:
        logger.warning(f"[Audit] 保存审计日志失败: {e}")


def run_all_collectors() -> dict[str, Any]:
    """
    执行所有已启用的采集器任务（串行）

    Returns:
        任务执行结果
    """
    print("🚀 开始串行采集...")

    collectors = list_enabled_collectors()
    total_result = {"total": 0, "success": 0, "failed": 0}

    for i, name in enumerate(collectors, 1):
        print(f"  [{i}/{len(collectors)}] {name}...", end=" ", flush=True)
        try:
            result = run_collector(name)
            total_result["total"] += result["total"]
            total_result["success"] += result["success"]
            total_result["failed"] += result["failed"]
            print(f"✓ ({result['total']}条)")
        except Exception:
            print("✗ 失败")
            continue

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

    print(f"🚀 开始并行采集: {', '.join(collector_names)}")

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
                print(f"  ✓ {name} ({result['total']}条)")
            except Exception:
                print(f"  ✗ {name} 失败")

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
