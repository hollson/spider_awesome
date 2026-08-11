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
from src.storage.mysql_store import MySQLStorage


def cmd_run(args):
    """执行单次采集"""
    _print_banner()
    collector_name = args.source
    logger.info(f"开始采集: {collector_name}")

    try:
        # 采集
        collector = get_collector(collector_name)
        records = collector.fetch()
        logger.info(f"采集到 {len(records)} 条数据")

        # 清洗
        cleaner = Cleaner()
        records = cleaner.process(records)

        # 校验
        validator = Validator()
        records = validator.process(records)

        # 存储
        if not args.dry_run:
            storage = MySQLStorage(auto_create=True)
            saved = storage.save(records)
            logger.info(f"保存 {saved} 条数据到数据库")
        else:
            logger.info("[Dry Run] 跳过数据库保存")
            for r in records[:3]:
                logger.info(f"  Sample: {r.get('source')} - {r.get('title')}")

    except Exception as e:
        logger.error(f"采集失败: {e}")
        sys.exit(1)


def cmd_run_all(args):
    """执行所有采集器"""
    _print_banner()
    from src.scheduler.tasks import run_all_collectors

    logger.info("开始执行所有采集任务")
    result = run_all_collectors()

    if not args.dry_run:
        logger.info(f"采集完成: 成功 {result['success']}/{result['total']}")


def cmd_run_parallel(args):
    """并行执行采集器"""
    _print_banner()
    from src.scheduler.tasks import run_parallel_collectors

    # 解析采集器列表
    collector_names = args.collectors.split(",") if args.collectors else None

    logger.info("开始并行采集任务")
    result = run_parallel_collectors(collector_names)

    if not args.dry_run:
        logger.info(f"并行采集完成: 成功 {result['success']}/{result['total']}")


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


def cmd_list(args):
    """列出所有采集器"""
    from src.collector import get_collector_config

    collectors = list_collectors()
    enabled = list_enabled_collectors()
    config = get_collector_config()

    print("\n可用的采集器:")
    print("-" * 60)
    print(f"  {'名称':<15} {'状态':<10} {'调度时间':<20}")
    print("-" * 60)

    for name in collectors:
        status = "✅ 启用" if name in enabled else "❌ 禁用"
        collector_config = config.get("collectors", {}).get(name, {})
        cron = collector_config.get("cron", "默认")
        print(f"  {name:<15} {status:<10} {cron:<20}")

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

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
