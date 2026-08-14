"""
采集审计日志表
记录每次采集周期的执行结果，用于监控、统计、问题追踪
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.storage.entities.base import Base


def _utcnow():
    """获取当前 UTC 时间（带时区）"""
    return datetime.now(UTC)


class CollectLog(Base):
    """采集审计日志表"""

    __tablename__ = "collect_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    collector_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="采集器名称")
    status: Mapped[str] = mapped_column(String(10), nullable=False, comment="执行状态: success/partial/fail")
    data_count: Mapped[int | None] = mapped_column(Integer, default=0, comment="采集数据条数")
    new_count: Mapped[int | None] = mapped_column(Integer, default=0, comment="新增条数")
    update_count: Mapped[int | None] = mapped_column(Integer, default=0, comment="更新条数")
    duplicate_count: Mapped[int | None] = mapped_column(Integer, default=0, comment="去重条数")
    duration: Mapped[float | None] = mapped_column(Float, comment="执行耗时(秒)")
    error_msg: Mapped[str | None] = mapped_column(Text, comment="错误信息(失败时)")
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True, comment="执行时间"
    )

    __table_args__ = (Index("idx_log_collector_time", "collector_name", "created_at"),)

    def __repr__(self) -> str:
        return f"<CollectLog {self.collector_name} {self.status} {self.created_at}>"
