"""
通用数据记录表
包含所有类型爬虫都需要的公共字段

衍生项目可直接使用此表，或参考创建自己的数据模型
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Index, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.entities.base import Base


def _utcnow():
    """获取当前 UTC 时间（带时区）"""
    return datetime.now(UTC)


class BaseRecord(Base):
    """通用数据记录表"""

    __tablename__ = "base_records"

    # 主键
    id: Mapped[str] = mapped_column(String(64), primary_key=True, comment="数据唯一标识（MD5）")

    # 来源信息
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="数据来源")
    collector_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="采集器名称")

    # 核心字段
    title: Mapped[str | None] = mapped_column(String(200), comment="标题")
    description: Mapped[str | None] = mapped_column(Text, comment="描述")
    url: Mapped[str | None] = mapped_column(String(500), comment="数据源 URL")

    # 扩展字段（JSON 格式，存储业务特定数据）
    raw_data: Mapped[Any | None] = mapped_column(JSON, comment="原始数据（JSON）")
    extra: Mapped[Any | None] = mapped_column(JSON, comment="扩展字段（业务特定数据）")

    # 状态字段
    status: Mapped[int | None] = mapped_column(SmallInteger, default=0, comment="数据状态 (0:正常, 1:删除)")

    # 时间戳
    create_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=_utcnow, comment="创建时间")
    update_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, comment="更新时间"
    )

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
