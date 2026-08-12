"""
数据采集模板项目 - 主入口
支持多种运行模式：采集、调度
"""

import argparse
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载环境配置（必须在其他模块导入之前）
import src.env_loader  # noqa: F401
from src.collector import get_collector, list_collectors, list_enabled_collectors
from src.common.logger import logger
from src.processor.cleaner import Cleaner
from src.processor.validator import Validator
from src.settings import settings
from src.storage.store import DataStorage


def cmd_run(args):
    """执行单次采集"""
    _print_banner()
    collector_name = args.source
    logger.info(f"开始采集: {collector_name}")

    # 采集（使用 safe_fetch，异常自动降级）
    collector = get_collector(collector_name)
    records = collector.safe_fetch()

    if not records:
        logger.warning(f"采集失败: {collector_name}，未获取到数据")
        sys.exit(1)

    logger.info(f"采集到 {len(records)} 条数据")

    # 清洗
    cleaner = Cleaner()
    records = cleaner.process(records)

    # 校验
    validator = Validator()
    records = validator.process(records)

    # 存储
    if not args.dry_run:
        storage = DataStorage(auto_create=True)
        saved = storage.save(records)
        logger.info(f"保存 {saved} 条数据到数据库")
    else:
        logger.info("[Dry Run] 跳过数据库保存")
        for r in records[:3]:
            logger.info(f"  Sample: {r.get('source')} - {r.get('title')}")


def cmd_run_all(args):
    """执行所有采集器"""
    _print_banner()
    from src.scheduler.tasks import run_all_collectors

    print("⏳ 开始执行所有采集任务...")
    result = run_all_collectors()

    print(f"\n{'=' * 50}")
    print("✅ 采集完成！")
    print(f"   总计: {result['total']} 条")
    print(f"   新增: {result['success']} 条")
    print(f"   去重: {result['failed']} 条")
    print(f"{'=' * 50}\n")


def cmd_run_parallel(args):
    """并行执行采集器"""
    _print_banner()
    from src.scheduler.tasks import run_parallel_collectors

    # 解析采集器列表
    collector_names = args.collectors.split(",") if args.collectors else None

    print("⏳ 开始并行采集任务...")
    result = run_parallel_collectors(collector_names)

    print(f"\n{'=' * 50}")
    print("✅ 并行采集完成！")
    print(f"   总计: {result['total']} 条")
    print(f"   新增: {result['success']} 条")
    print(f"   去重: {result['failed']} 条")
    print(f"{'=' * 50}\n")


def cmd_scheduler(args):
    """启动定时调度"""
    _print_banner()
    from src.collector import get_collector_schedule
    from src.scheduler.task_manager import task_manager
    from src.scheduler.tasks import parse_cron_to_hour_minute, run_all_collectors, run_parallel_collectors

    logger.info("启动定时调度模式")

    # 获取已启用的采集器
    enabled_collectors = list_enabled_collectors()
    parallel_mode = settings.SCHEDULER_PARALLEL

    if parallel_mode:
        # 并行模式：所有采集器并行执行
        task_id = "parallel_collect"
        task_manager.add_cron_job(
            job_id=task_id,
            func=run_parallel_collectors,
            hour=settings.MAX_WORKERS,  # 使用默认调度时间
            minute=0,
        )
        logger.info(f"添加并行采集任务: {task_id}")
    else:
        # 串行模式：每个采集器独立调度
        for collector_name in enabled_collectors:
            schedule = get_collector_schedule(collector_name)
            cron = schedule.get("cron", "0 0 * * *")
            hour, minute = parse_cron_to_hour_minute(cron)

            task_id = f"collect_{collector_name}"
            task_manager.add_cron_job(
                job_id=task_id,
                func=lambda name=collector_name: run_all_collectors(),
                hour=hour,
                minute=minute,
            )
            logger.info(f"添加采集任务: {task_id} (cron: {cron})")

    # 启动调度器
    task_manager.start()
    logger.info("调度器已启动，按 Ctrl+C 停止")
    logger.info("任务列表:")
    task_manager.list_jobs()

    try:
        while True:
            import time

            time.sleep(1)
    except KeyboardInterrupt:
        task_manager.stop()
        logger.info("调度器已停止")


def _cron_to_chinese(cron: str) -> str:
    """将 cron 表达式转为中文说明"""
    parts = cron.strip().split()
    if len(parts) < 5:
        return cron

    minute, hour, day, month, weekday = parts

    # 每 N 分钟
    if minute.startswith("*/") and hour == "*":
        return f"每 {minute[2:]} 分钟"

    # 每 N 小时（整点）
    if minute == "0" and hour.startswith("*/"):
        return f"每 {hour[2:]} 小时"

    # 固定时间
    if minute.isdigit() and hour.isdigit() and day == "*" and month == "*":
        if weekday == "*":
            return f"每天 {hour}:{minute.zfill(2)}"
        weekday_map = {"0": "日", "1": "一", "2": "二", "3": "三", "4": "四", "5": "五", "6": "六"}
        if "-" in weekday:
            w_parts = weekday.split("-")
            w1 = weekday_map.get(w_parts[0], w_parts[0])
            w2 = weekday_map.get(w_parts[1], w_parts[1])
            return f"周{w1}-{w2} {hour}:{minute.zfill(2)}"
        w = weekday_map.get(weekday, weekday)
        return f"每周{w} {hour}:{minute.zfill(2)}"

    return cron


def cmd_list(args):
    """列出所有采集器"""
    from src.collector.registry import get_collector_schedule

    collectors = list_collectors()
    enabled = list_enabled_collectors()

    print("\n可用的采集器:")
    print("-" * 65)
    print(f"  {'名称':<15} {'状态':<10} {'调度':<20} {'说明'}")
    print("-" * 65)

    for name in collectors:
        status = "✅ 启用" if name in enabled else "❌ 禁用"
        schedule = get_collector_schedule(name)
        cron = schedule.get("cron", "未知")
        desc = _cron_to_chinese(cron)
        print(f"  {name:<15} {status:<10} {cron:<20} {desc}")

    print()


def cmd_status(args):
    """查看任务状态"""
    from src.scheduler.task_manager import task_manager

    status = task_manager.get_all_status()
    if not status:
        print("暂无任务执行记录")
        return

    print("\n任务执行状态:")
    print("-" * 60)
    for record in status:
        print(
            f"  {record['task_id']}: {record['status']} "
            f"(耗时 {record['duration']}s, "
            f"成功 {record['success_count']}/{record['total_count']})"
        )


def cmd_logs(args):
    """查看采集审计日志"""
    from datetime import datetime, timedelta

    from src.storage.models import CollectLog
    from src.storage.session import get_db_instance

    # 参数处理
    limit = args.limit or 20
    collector = args.collector
    hours = args.hours or 24

    with get_db_instance().get_session() as session:
        query = session.query(CollectLog)

        # 时间范围
        since = datetime.now() - timedelta(hours=hours)
        query = query.filter(CollectLog.created_at >= since)

        # 采集器过滤
        if collector:
            query = query.filter(CollectLog.collector_name == collector)

        # 按时间倒序，转换为字典列表
        logs = [
            {
                "collector_name": log.collector_name,
                "status": log.status,
                "data_count": log.data_count,
                "duration": log.duration,
                "error_msg": log.error_msg,
                "created_at": log.created_at,
            }
            for log in query.order_by(CollectLog.created_at.desc()).limit(limit).all()
        ]

    if not logs:
        print(f"\n最近 {hours} 小时内无采集记录")
        return

    print(f"\n采集审计日志 (最近 {hours} 小时，共 {len(logs)} 条):")
    print("-" * 80)
    print(f"  {'时间':<20} {'采集器':<15} {'状态':<10} {'数据量':<10} {'耗时':<10}")
    print("-" * 80)

    for log in logs:
        status_icon = "✅" if log["status"] == "success" else "❌"
        time_str = log["created_at"].strftime("%m-%d %H:%M:%S") if log["created_at"] else "-"
        print(
            f"  {time_str:<20} {log['collector_name']:<15} "
            f"{status_icon} {log['status']:<8} {log['data_count']:<10} {log['duration'] or 0:.1f}s"
        )

    print()

    # 显示失败详情
    failed_logs = [log for log in logs if log["status"] == "fail" and log["error_msg"]]
    if failed_logs:
        print("失败详情:")
        print("-" * 80)
        for log in failed_logs[:5]:  # 只显示最近5条失败
            print(f"  [{log['collector_name']}] {log['error_msg'][:60]}")
        print()


def _print_banner():
    """打印启动横幅"""
    from src.common.color import banner_label, banner_line, banner_title

    db_display = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "SQLite"
    print(banner_line())
    print(banner_title(f"  启动 {settings.APP_NAME} v{settings.APP_VERSION}"))
    print(banner_label("环境", settings.ENV_MODE) + f" | 调试: {settings.DEBUG}")
    print(banner_label("数据库", db_display))
    print(banner_label("日志级别", settings.LOG_LEVEL))
    print(banner_line() + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="数据采集模板项目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python src/main.py run --source=alerion         # 执行单个采集器
  python src/main.py run-all                       # 执行所有采集器（串行）
  python src/main.py run-all --dry-run             # 试运行（不保存）
  python src/main.py run-parallel                  # 并行执行所有采集器
  python src/main.py run-parallel --collectors=alerion,asl  # 并行指定采集器
  python src/main.py scheduler                     # 启动定时调度
  python src/main.py list                          # 列出所有采集器
  python src/main.py status                        # 查看任务状态
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # run 命令
    run_parser = subparsers.add_parser("run", help="执行单个采集器")
    run_parser.add_argument("--source", "-s", required=True, help="采集器名称")
    run_parser.add_argument("--dry-run", action="store_true", help="仅采集不保存")
    run_parser.set_defaults(func=cmd_run)

    # run-all 命令
    run_all_parser = subparsers.add_parser("run-all", help="执行所有采集器（串行）")
    run_all_parser.add_argument("--dry-run", action="store_true", help="仅采集不保存")
    run_all_parser.set_defaults(func=cmd_run_all)

    # run-parallel 命令
    run_parallel_parser = subparsers.add_parser("run-parallel", help="并行执行采集器")
    run_parallel_parser.add_argument("--collectors", "-c", help="采集器列表（逗号分隔）")
    run_parallel_parser.add_argument("--dry-run", action="store_true", help="仅采集不保存")
    run_parallel_parser.set_defaults(func=cmd_run_parallel)

    # scheduler 命令
    scheduler_parser = subparsers.add_parser("scheduler", help="启动定时调度")
    scheduler_parser.set_defaults(func=cmd_scheduler)

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出所有采集器")
    list_parser.set_defaults(func=cmd_list)

    # status 命令
    status_parser = subparsers.add_parser("status", help="查看任务状态")
    status_parser.set_defaults(func=cmd_status)

    # logs 命令
    logs_parser = subparsers.add_parser("logs", help="查看采集审计日志")
    logs_parser.add_argument("--limit", "-l", type=int, default=20, help="显示条数 (默认20)")
    logs_parser.add_argument("--collector", "-c", help="指定采集器名称")
    logs_parser.add_argument("--hours", type=int, default=24, help="查询最近N小时 (默认24)")
    logs_parser.set_defaults(func=cmd_logs)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
