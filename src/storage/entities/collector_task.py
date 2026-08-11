"""
采集任务记录表
记录每次采集任务的执行状态
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from src.storage.entities.base import Base


class CollectorTask(Base):
    """采集任务记录表"""

    __tablename__ = "collector_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collector_name = Column(String(50), nullable=False, comment="采集器名称")
    status = Column(String(20), default="pending", comment="任务状态")
    total_count = Column(Integer, default=0, comment="总数据量")
    success_count = Column(Integer, default=0, comment="成功数量")
    failed_count = Column(Integer, default=0, comment="失败数量")
    duplicate_count = Column(Integer, default=0, comment="重复数量")
    error_message = Column(Text, comment="错误信息")
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    create_time = Column(DateTime, default=datetime.utcnow, comment="创建时间")
