"""
航空业务数据记录表
包含航空业务特定字段

如果你的项目不是航空业务，请直接使用 BaseRecord
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Index, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.entities.base import Base


def _utcnow():
    """获取当前 UTC 时间（带时区）"""
    return datetime.now(UTC)


class DataRecord(Base):
    """航空业务数据记录表"""

    __tablename__ = "data_records"

    # 主键
    id: Mapped[str] = mapped_column(String(64), primary_key=True, comment="数据唯一标识（MD5）")

    # 来源信息
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="数据来源")
    collector_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="采集器名称")
    operator_id: Mapped[str | None] = mapped_column(String(64), comment="运营商 ID")

    # 核心字段
    title: Mapped[str | None] = mapped_column(String(200), comment="标题")
    description: Mapped[str | None] = mapped_column(Text, comment="描述")
    tail_num: Mapped[str | None] = mapped_column(String(20), comment="飞机尾号")
    model: Mapped[str | None] = mapped_column(String(50), comment="飞机型号")

    # 地理位置
    origin_code: Mapped[str | None] = mapped_column(String(20), index=True, comment="出发地编码")
    origin_city: Mapped[str | None] = mapped_column(String(100), comment="出发城市")
    origin_airport_id: Mapped[str | None] = mapped_column(String(64), comment="出发机场 ID")
    dest_code: Mapped[str | None] = mapped_column(String(20), index=True, comment="目的地编码")
    dest_city: Mapped[str | None] = mapped_column(String(100), comment="目的城市")
    dest_airport_id: Mapped[str | None] = mapped_column(String(64), comment="目的机场 ID")

    # 时间相关
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="开始时间")
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="结束时间")
    take_off_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="起飞时间")

    # 费用相关
    cost_minutes: Mapped[int | None] = mapped_column(Integer, comment="飞行时长（分钟）")
    flight_cost: Mapped[float | None] = mapped_column(Float, comment="报价/费用")
    currency: Mapped[str | None] = mapped_column(String(10), comment="币种")
    currency_symbol: Mapped[str | None] = mapped_column(String(10), comment="币种符号")

    # 其他字段
    seats: Mapped[int | None] = mapped_column(Integer, comment="剩余座位数")
    thumb: Mapped[str | None] = mapped_column(String(500), comment="缩略图 URL")
    preview: Mapped[Any | None] = mapped_column(JSON, comment="预览图列表")
    source_url: Mapped[str | None] = mapped_column(String(500), comment="数据源 URL")

    # 扩展字段
    raw_data: Mapped[Any | None] = mapped_column(JSON, comment="原始数据（JSON）")
    extra: Mapped[Any | None] = mapped_column(JSON, comment="扩展字段")

    # 状态字段
    is_hot: Mapped[int | None] = mapped_column(SmallInteger, default=0, comment="热门等级 (0-3)")
    sale_status: Mapped[int | None] = mapped_column(SmallInteger, default=0, comment="销售状态")
    status: Mapped[int | None] = mapped_column(SmallInteger, default=0, comment="数据状态 (0:正常, 1:删除)")

    # 时间戳
    create_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=_utcnow, comment="创建时间")
    update_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, comment="更新时间"
    )

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
