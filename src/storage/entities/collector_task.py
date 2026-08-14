"""
采集任务记录表
记录每次采集任务的执行状态
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.storage.entities.base import Base


def _utcnow():
    """获取当前 UTC 时间（带时区）"""
    return datetime.now(UTC)


class CollectorTask(Base):
    """采集任务记录表"""

    __tablename__ = "collector_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    collector_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="采集器名称")
    status: Mapped[str | None] = mapped_column(String(20), default="pending", comment="任务状态")
    total_count: Mapped[int | None] = mapped_column(Integer, default=0, comment="总数据量")
    success_count: Mapped[int | None] = mapped_column(Integer, default=0, comment="成功数量")
    failed_count: Mapped[int | None] = mapped_column(Integer, default=0, comment="失败数量")
    duplicate_count: Mapped[int | None] = mapped_column(Integer, default=0, comment="重复数量")
    error_message: Mapped[str | None] = mapped_column(Text, comment="错误信息")
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="开始时间")
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="结束时间")
    create_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=_utcnow, comment="创建时间")
