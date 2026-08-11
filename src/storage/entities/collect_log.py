"""
采集审计日志表
记录每次采集周期的执行结果，用于监控、统计、问题追踪
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text

from src.storage.entities.base import Base


class CollectLog(Base):
    """采集审计日志表"""

    __tablename__ = "collect_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collector_name = Column(String(50), nullable=False, index=True, comment="采集器名称")
    status = Column(String(10), nullable=False, comment="执行状态: success/partial/fail")
    data_count = Column(Integer, default=0, comment="采集数据条数")
    new_count = Column(Integer, default=0, comment="新增条数")
    update_count = Column(Integer, default=0, comment="更新条数")
    duplicate_count = Column(Integer, default=0, comment="去重条数")
    duration = Column(Float, comment="执行耗时(秒)")
    error_msg = Column(Text, comment="错误信息(失败时)")
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="执行时间")

    __table_args__ = (Index("idx_log_collector_time", "collector_name", "created_at"),)

    def __repr__(self) -> str:
        return f"<CollectLog {self.collector_name} {self.status} {self.created_at}>"
