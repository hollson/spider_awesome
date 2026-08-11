"""
调度层模块
使用 APScheduler 实现定时采集任务，支持并发控制、失败重试、状态管理
"""

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from threading import Lock

from src.common.logger import logger


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class TaskRecord:
    """任务执行记录"""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = TaskStatus.PENDING
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.duration: float = 0
        self.total_count: int = 0
        self.success_count: int = 0
        self.failed_count: int = 0
        self.error_message: str = ""
        self.retry_count: int = 0

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": round(self.duration, 2),
            "total_count": self.total_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }


class TaskManager:
    """
    任务管理器

    功能：
    - 管理定时采集任务
    - 支持动态启停
    - 任务并发控制（线程池）
    - 失败自动重试
    - 任务状态追踪
    """

    def __init__(
        self,
        max_workers: int = 5,
        task_timeout: int = 300,
        retry_count: int = 3,
        retry_delay: int = 60,
    ):
        """
        初始化任务管理器

        Args:
            max_workers: 最大并发任务数
            task_timeout: 单任务超时时间（秒）
            retry_count: 失败重试次数
            retry_delay: 重试间隔（秒）
        """
        self.max_workers = max_workers
        self.task_timeout = task_timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay

        self._scheduler = None
        self._executor: ThreadPoolExecutor | None = None
        self._tasks: dict[str, dict] = {}
        self._records: dict[str, TaskRecord] = {}
        self._lock = Lock()

    def _get_scheduler(self):
        """获取 APScheduler 实例"""
        if self._scheduler is None:
            try:
                from apscheduler.schedulers.background import BackgroundScheduler

                self._scheduler = BackgroundScheduler()
            except ImportError:
                logger.error("APScheduler 未安装，请执行: uv add apscheduler")
                raise
        return self._scheduler

    def _get_executor(self) -> ThreadPoolExecutor:
        """获取线程池执行器"""
        if self._executor is None:
            self._executor = ThreadPoolExecutor(
                max_workers=self.max_workers, thread_name_prefix="collector"
            )
        return self._executor

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
            func=self._wrap_task(job_id, func),
            trigger="cron",
            id=job_id,
            hour=hour,
            minute=minute,
            replace_existing=True,
            **kwargs,
        )
        self._tasks[job_id] = {
            "func": func,
            "trigger": "cron",
            "hour": hour,
            "minute": minute,
        }
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
            func=self._wrap_task(job_id, func),
            trigger="interval",
            id=job_id,
            minutes=minutes,
            replace_existing=True,
            **kwargs,
        )
        self._tasks[job_id] = {
            "func": func,
            "trigger": "interval",
            "minutes": minutes,
        }
        logger.info(f"[Scheduler] 添加间隔任务: {job_id} (每 {minutes} 分钟)")

    def _wrap_task(self, task_id: str, func: Callable) -> Callable:
        """包装任务函数，添加并发控制和状态管理"""

        def wrapper():
            self._run_task_with_retry(task_id, func)

        return wrapper

    def _run_task_with_retry(self, task_id: str, func: Callable):
        """
        带重试的任务执行

        Args:
            task_id: 任务 ID
            func: 任务函数
        """
        record = TaskRecord(task_id)
        with self._lock:
            self._records[task_id] = record

        for attempt in range(self.retry_count + 1):
            try:
                record.status = TaskStatus.RUNNING if attempt == 0 else TaskStatus.RETRYING
                record.start_time = datetime.now()
                record.retry_count = attempt

                if attempt > 0:
                    logger.info(f"[Scheduler] 重试任务 {task_id} (第 {attempt} 次)")

                # 执行任务
                result = func()

                # 记录成功
                record.status = TaskStatus.SUCCESS
                record.end_time = datetime.now()
                record.duration = (record.end_time - record.start_time).total_seconds()

                if isinstance(result, dict):
                    record.total_count = result.get("total", 0)
                    record.success_count = result.get("success", 0)
                    record.failed_count = result.get("failed", 0)

                logger.info(
                    f"[Scheduler] 任务 {task_id} 完成 "
                    f"(耗时 {record.duration:.1f}s, "
                    f"成功 {record.success_count}/{record.total_count})"
                )
                return

            except Exception as e:
                record.error_message = str(e)
                logger.warning(f"[Scheduler] 任务 {task_id} 失败: {e}")

                if attempt < self.retry_count:
                    logger.info(f"[Scheduler] {self.retry_delay}s 后重试...")
                    time.sleep(self.retry_delay)
                else:
                    record.status = TaskStatus.FAILED
                    record.end_time = datetime.now()
                    record.duration = (record.end_time - record.start_time).total_seconds()
                    logger.error(
                        f"[Scheduler] 任务 {task_id} 最终失败 (已重试 {self.retry_count} 次)"
                    )

    def submit_task(self, task_id: str, func: Callable) -> str:
        """
        提交异步任务到线程池

        Args:
            task_id: 任务 ID
            func: 任务函数

        Returns:
            任务 ID
        """
        executor = self._get_executor()
        executor.submit(self._run_task_with_retry, task_id, func)
        return task_id

    def start(self):
        """启动调度器"""
        scheduler = self._get_scheduler()
        if not scheduler.running:
            scheduler.start()
            logger.info("[Scheduler] 调度器已启动")

    def stop(self):
        """停止调度器"""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=True)
            logger.info("[Scheduler] 调度器已停止")

        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

    def get_task_status(self, task_id: str) -> dict | None:
        """获取任务状态"""
        record = self._records.get(task_id)
        return record.to_dict() if record else None

    def get_all_status(self) -> list[dict]:
        """获取所有任务状态"""
        return [record.to_dict() for record in self._records.values()]

    def list_jobs(self):
        """列出所有任务"""
        for job_id, config in self._tasks.items():
            logger.info(f"  - {job_id}: {config}")


# 全局任务管理器实例
task_manager = TaskManager()
