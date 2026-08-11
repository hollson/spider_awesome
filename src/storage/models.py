"""
SQLAlchemy ORM 数据模型
定义所有数据表结构

设计原则：
- BaseRecord: 公共基础字段，适用于所有类型的爬虫
- DataRecord: 航空业务专用表，包含业务特定字段
- 其他业务可参考 BaseRecord 创建自己的数据模型
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BaseRecord(Base):
    """
    通用数据记录表
    包含所有类型爬虫都需要的公共字段

    衍生项目可直接使用此表，或参考创建自己的数据模型
    """

    __tablename__ = "base_records"

    # 主键
    id = Column(String(64), primary_key=True, comment="数据唯一标识（MD5）")

    # 来源信息
    source = Column(String(50), nullable=False, index=True, comment="数据来源")
    collector_name = Column(String(50), nullable=False, comment="采集器名称")

    # 核心字段
    title = Column(String(200), comment="标题")
    description = Column(Text, comment="描述")
    url = Column(String(500), comment="数据源 URL")

    # 扩展字段（JSON 格式，存储业务特定数据）
    raw_data = Column(JSON, comment="原始数据（JSON）")
    extra = Column(JSON, comment="扩展字段（业务特定数据）")

    # 状态字段
    status = Column(SmallInteger, default=0, comment="数据状态 (0:正常, 1:删除)")

    # 时间戳
    create_time = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 索引
    __table_args__ = (Index("idx_source_create", "source", "create_time"),)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "source": self.source,
            "collector_name": self.collector_name,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "status": self.status,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "update_time": self.update_time.isoformat() if self.update_time else None,
        }


class DataRecord(Base):
    """
    航空业务数据记录表
    包含航空业务特定字段

    如果你的项目不是航空业务，请直接使用 BaseRecord
    """

    __tablename__ = "data_records"

    # 主键
    id = Column(String(64), primary_key=True, comment="数据唯一标识（MD5）")

    # 来源信息
    source = Column(String(50), nullable=False, index=True, comment="数据来源")
    collector_name = Column(String(50), nullable=False, comment="采集器名称")
    operator_id = Column(String(64), comment="运营商 ID")

    # 核心字段
    title = Column(String(200), comment="标题")
    description = Column(Text, comment="描述")
    tail_num = Column(String(20), comment="飞机尾号")
    model = Column(String(50), comment="飞机型号")

    # 地理位置
    origin_code = Column(String(20), index=True, comment="出发地编码")
    origin_city = Column(String(100), comment="出发城市")
    origin_airport_id = Column(String(64), comment="出发机场 ID")
    dest_code = Column(String(20), index=True, comment="目的地编码")
    dest_city = Column(String(100), comment="目的城市")
    dest_airport_id = Column(String(64), comment="目的机场 ID")

    # 时间相关
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    take_off_time = Column(DateTime, comment="起飞时间")

    # 费用相关
    cost_minutes = Column(Integer, comment="飞行时长（分钟）")
    flight_cost = Column(Float, comment="报价/费用")
    currency = Column(String(10), comment="币种")
    currency_symbol = Column(String(10), comment="币种符号")

    # 其他字段
    seats = Column(Integer, comment="剩余座位数")
    thumb = Column(String(500), comment="缩略图 URL")
    preview = Column(JSON, comment="预览图列表")
    source_url = Column(String(500), comment="数据源 URL")

    # 扩展字段
    raw_data = Column(JSON, comment="原始数据（JSON）")
    extra = Column(JSON, comment="扩展字段")

    # 状态字段
    is_hot = Column(SmallInteger, default=0, comment="热门等级 (0-3)")
    sale_status = Column(SmallInteger, default=0, comment="销售状态")
    status = Column(SmallInteger, default=0, comment="数据状态 (0:正常, 1:删除)")

    # 时间戳
    create_time = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 索引
    __table_args__ = (
        Index("idx_source_time", "source", "start_time"),
        Index("idx_route", "origin_code", "dest_code"),
    )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "source": self.source,
            "collector_name": self.collector_name,
            "operator_id": self.operator_id,
            "title": self.title,
            "description": self.description,
            "tail_num": self.tail_num,
            "model": self.model,
            "origin_code": self.origin_code,
            "origin_city": self.origin_city,
            "dest_code": self.dest_code,
            "dest_city": self.dest_city,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "take_off_time": self.take_off_time.isoformat() if self.take_off_time else None,
            "cost_minutes": self.cost_minutes,
            "flight_cost": self.flight_cost,
            "currency": self.currency,
            "currency_symbol": self.currency_symbol,
            "seats": self.seats,
            "thumb": self.thumb,
            "source_url": self.source_url,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }


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


class CollectLog(Base):
    """
    采集审计日志表
    记录每次采集周期的执行结果，用于监控、统计、问题追踪
    """

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
