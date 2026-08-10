"""
数据采集模板项目 - 主入口
支持多种运行模式：采集、调度、API 服务
"""
import argparse
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载环境配置（必须在其他模块导入之前）
import src.env_loader  # noqa: F401

from src.common.logger import logger
from src.collector import list_collectors, get_collector
from src.processor.cleaner import Cleaner
from src.processor.validator import Validator
from src.storage.mysql_store import MySQLStorage
from src.settings import settings


def cmd_run(args):
    """执行单次采集"""
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
    logger.info("开始执行所有采集任务")

    collectors = list_collectors()
    logger.info(f"可用采集器: {collectors}")

    cleaner = Cleaner()
    validator = Validator()
    storage = MySQLStorage(auto_create=True) if not args.dry_run else None

    for name in collectors:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"采集器: {name}")
            logger.info(f"{'='*50}")

            collector = get_collector(name)
            records = collector.fetch()
            records = cleaner.process(records)
            records = validator.process(records)

            if storage:
                saved = storage.save(records)
                logger.info(f"[{name}] 保存 {saved} 条数据")
            else:
                logger.info(f"[{name}] 采集 {len(records)} 条数据 (Dry Run)")

        except Exception as e:
            logger.error(f"[{name}] 采集失败: {e}")
            continue


def cmd_scheduler(args):
    """启动定时调度"""
    from src.scheduler.task_manager import task_manager
    from src.scheduler.tasks import run_all_collectors

    logger.info("启动定时调度模式")

    # 添加定时任务
    task_manager.add_cron_job(
        job_id="daily_collect",
        func=run_all_collectors,
        hour=settings.COLLECTOR_CRON_HOUR,
        minute=settings.COLLECTOR_CRON_MINUTE,
    )

    # 启动调度器
    task_manager.start()
    logger.info(f"调度器已启动，每天 {settings.COLLECTOR_CRON_HOUR:02d}:{settings.COLLECTOR_CRON_MINUTE:02d} 执行采集")
    logger.info("按 Ctrl+C 停止")

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        task_manager.stop()
        logger.info("调度器已停止")


def cmd_api(args):
    """启动 API 服务"""
    logger.info("启动 API 服务模式")

    try:
        import uvicorn
        uvicorn.run(
            "src.expose.server:app",
            host=settings.SERVER_HOST,
            port=settings.SERVER_PORT,
            reload=args.reload,
        )
    except ImportError:
        logger.error("uvicorn 未安装，请执行: pip install uvicorn")
        sys.exit(1)


def cmd_list(args):
    """列出所有采集器"""
    collectors = list_collectors()
    print("\n可用的采集器:")
    print("-" * 40)
    for name in collectors:
        print(f"  - {name}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="数据采集模板项目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python src/main.py run --source=alerion     # 执行单个采集器
  python src/main.py run-all                   # 执行所有采集器
  python src/main.py run-all --dry-run         # 执行所有采集器（不保存）
  python src/main.py scheduler                 # 启动定时调度
  python src/main.py api                       # 启动 API 服务
  python src/main.py list                      # 列出所有采集器
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # run 命令
    run_parser = subparsers.add_parser("run", help="执行单个采集器")
    run_parser.add_argument("--source", "-s", required=True, help="采集器名称")
    run_parser.add_argument("--dry-run", action="store_true", help="仅采集不保存")
    run_parser.set_defaults(func=cmd_run)

    # run-all 命令
    run_all_parser = subparsers.add_parser("run-all", help="执行所有采集器")
    run_all_parser.add_argument("--dry-run", action="store_true", help="仅采集不保存")
    run_all_parser.set_defaults(func=cmd_run_all)

    # scheduler 命令
    scheduler_parser = subparsers.add_parser("scheduler", help="启动定时调度")
    scheduler_parser.set_defaults(func=cmd_scheduler)

    # api 命令
    api_parser = subparsers.add_parser("api", help="启动 API 服务")
    api_parser.add_argument("--reload", action="store_true", help="热重载模式")
    api_parser.set_defaults(func=cmd_api)

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出所有采集器")
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
