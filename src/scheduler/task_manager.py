"""
调度层模块
使用 APScheduler 实现定时采集任务
"""
from datetime import datetime
from typing import Callable, Optional

from src.common.logger import logger


class TaskManager:
    """
    任务管理器

    功能：
    - 管理定时采集任务
    - 支持动态启停
    - 任务并发控制
    """

    def __init__(self):
        self._scheduler = None
        self._tasks = {}

    def _get_scheduler(self):
        """获取 APScheduler 实例"""
        if self._scheduler is None:
            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                self._scheduler = BackgroundScheduler()
            except ImportError:
                logger.error("APScheduler 未安装，请执行: pip install apscheduler")
                raise
        return self._scheduler

    def add_cron_job(
        self,
        job_id: str,
        func: Callable,
        hour: int = 0,
        minute: int = 0,
        **kwargs,
    ):
        """
        添加 Cron 定时任务

        Args:
            job_id: 任务 ID
            func: 任务函数
            hour: 执行小时
            minute: 执行分钟
        """
        scheduler = self._get_scheduler()
        scheduler.add_job(
            func=func,
            trigger="cron",
            id=job_id,
            hour=hour,
            minute=minute,
            replace_existing=True,
            **kwargs,
        )
        self._tasks[job_id] = {"func": func, "hour": hour, "minute": minute}
        logger.info(f"[Scheduler] 添加定时任务: {job_id} (每天 {hour:02d}:{minute:02d})")

    def add_interval_job(
        self,
        job_id: str,
        func: Callable,
        minutes: int = 60,
        **kwargs,
    ):
        """
        添加间隔定时任务

        Args:
            job_id: 任务 ID
            func: 任务函数
            minutes: 间隔分钟数
        """
        scheduler = self._get_scheduler()
        scheduler.add_job(
            func=func,
            trigger="interval",
            id=job_id,
            minutes=minutes,
            replace_existing=True,
            **kwargs,
        )
        self._tasks[job_id] = {"func": func, "minutes": minutes}
        logger.info(f"[Scheduler] 添加间隔任务: {job_id} (每 {minutes} 分钟)")

    def start(self):
        """启动调度器"""
        scheduler = self._get_scheduler()
        if not scheduler.running:
            scheduler.start()
            logger.info("[Scheduler] 调度器已启动")

    def stop(self):
        """停止调度器"""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("[Scheduler] 调度器已停止")

    def list_jobs(self):
        """列出所有任务"""
        for job_id, config in self._tasks.items():
            logger.info(f"  - {job_id}: {config}")


# 全局任务管理器实例
task_manager = TaskManager()
