"""
MySQL 存储实现
使用 SQLAlchemy 进行数据持久化

支持两种存储模式：
- BaseStorage: 通用存储，使用 BaseRecord 表，适用于所有类型的爬虫
- MySQLStorage: 航空业务存储，使用 DataRecord 表，包含航空业务特定字段
"""

from typing import Any

from sqlalchemy import func

from src.common.logger import logger
from src.storage.base_storage import BaseStorage
from src.storage.models import BaseRecord, DataRecord
from src.storage.session import db


class BaseRecordStorage(BaseStorage):
    """
    通用数据存储（使用 BaseRecord 表）

    适用于所有类型的爬虫，只包含公共字段
    衍生项目可直接使用此类
    """

    def __init__(self, auto_create: bool = True):
        """
        初始化存储

        Args:
            auto_create: 是否自动创建表
        """
        if auto_create:
            db.create_tables()

    def save(self, records: list[dict[str, Any]]) -> int:
        """
        保存数据

        Args:
            records: 待保存的数据列表

        Returns:
            成功保存的数量
        """
        if not records:
            return 0

        logger.info(f"[BaseRecordStorage] 开始保存 {len(records)} 条数据")
        saved_count = 0
        with db.get_session() as session:
            for record in records:
                try:
                    record_id = record.get("id")
                    if not record_id:
                        continue

                    # 检查是否已存在
                    existing = session.query(BaseRecord).filter_by(id=record_id).first()
                    if existing:
                        logger.debug(f"记录已存在，跳过: {record_id}")
                        continue

                    # 创建新记录（只保存公共字段）
                    db_record = BaseRecord(
                        id=record_id,
                        source=record.get("source", ""),
                        collector_name=record.get("collector_name", ""),
                        title=record.get("title"),
                        description=record.get("description"),
                        url=record.get("url") or record.get("source_url"),
                        raw_data=record.get("raw_data"),
                        extra=record.get("extra"),
                    )
                    session.add(db_record)
                    saved_count += 1
                    logger.debug(f"记录保存成功: {record_id}")
                except Exception as e:
                    logger.warning(f"记录保存失败: {record.get('id')} - {e}")
                    continue

            session.commit()

        logger.info(f"[BaseRecordStorage] 保存完成: {saved_count}/{len(records)} 条")
        return saved_count

    def exists(self, record_id: str) -> bool:
        """检查数据是否存在"""
        with db.get_session() as session:
            return session.query(BaseRecord).filter_by(id=record_id).count() > 0

    def count(self, filters: dict[str, Any] | None = None) -> int:
        """统计数据数量"""
        with db.get_session() as session:
            query = session.query(func.count(BaseRecord.id))
            if filters:
                if "source" in filters:
                    query = query.filter(BaseRecord.source == filters["source"])
                if "collector_name" in filters:
                    query = query.filter(BaseRecord.collector_name == filters["collector_name"])
            return query.scalar()

    def query(
        self,
        source: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        查询数据

        Args:
            source: 数据来源
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            数据列表
        """
        with db.get_session() as session:
            query = session.query(BaseRecord)

            if source:
                query = query.filter(BaseRecord.source == source)

            records = query.order_by(BaseRecord.create_time.desc()).offset(offset).limit(limit).all()
            return [r.to_dict() for r in records]


class MySQLStorage(BaseRecordStorage):
    """
    航空业务数据存储（使用 DataRecord 表）

    继承 BaseRecordStorage，添加航空业务特定字段的支持
    如果你的项目不是航空业务，请直接使用 BaseRecordStorage
    """

    def save(self, records: list[dict[str, Any]]) -> int:
        """
        保存航空业务数据

        Args:
            records: 待保存的数据列表

        Returns:
            成功保存的数量
        """
        if not records:
            return 0

        logger.info(f"[MySQLStorage] 开始保存 {len(records)} 条数据")
        saved_count = 0
        with db.get_session() as session:
            for record in records:
                try:
                    record_id = record.get("id")
                    if not record_id:
                        continue

                    # 检查是否已存在
                    existing = session.query(DataRecord).filter_by(id=record_id).first()
                    if existing:
                        logger.debug(f"记录已存在，跳过: {record_id}")
                        continue

                    # 创建新记录（包含航空业务特定字段）
                    db_record = DataRecord(
                        # 公共字段
                        id=record_id,
                        source=record.get("source", ""),
                        collector_name=record.get("collector_name", ""),
                        title=record.get("title"),
                        description=record.get("description"),
                        url=record.get("url") or record.get("source_url"),
                        raw_data=record.get("raw_data"),
                        extra=record.get("extra"),
                        # 航空业务字段
                        operator_id=record.get("operator_id"),
                        tail_num=record.get("tail_num"),
                        model=record.get("model"),
                        origin_code=record.get("origin_code"),
                        origin_city=record.get("origin_city"),
                        origin_airport_id=record.get("origin_airport_id"),
                        dest_code=record.get("dest_code"),
                        dest_city=record.get("dest_city"),
                        dest_airport_id=record.get("dest_airport_id"),
                        start_time=record.get("start_time"),
                        end_time=record.get("end_time"),
                        take_off_time=record.get("take_off_time"),
                        cost_minutes=record.get("cost_minutes"),
                        flight_cost=record.get("flight_cost"),
                        currency=record.get("currency"),
                        currency_symbol=record.get("currency_symbol"),
                        seats=record.get("seats"),
                        thumb=record.get("thumb"),
                        preview=record.get("preview"),
                    )
                    session.add(db_record)
                    saved_count += 1
                    logger.debug(f"记录保存成功: {record_id}")
                except Exception as e:
                    logger.warning(f"记录保存失败: {record.get('id')} - {e}")
                    continue

            session.commit()

        logger.info(f"[MySQLStorage] 保存完成: {saved_count}/{len(records)} 条")
        return saved_count

    def query(
        self,
        source: str | None = None,
        origin_code: str | None = None,
        dest_code: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        查询航空业务数据

        Args:
            source: 数据来源
            origin_code: 出发地编码
            dest_code: 目的地编码
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            数据列表
        """
        with db.get_session() as session:
            query = session.query(DataRecord)

            if source:
                query = query.filter(DataRecord.source == source)
            if origin_code:
                query = query.filter(DataRecord.origin_code == origin_code)
            if dest_code:
                query = query.filter(DataRecord.dest_code == dest_code)

            records = query.order_by(DataRecord.create_time.desc()).offset(offset).limit(limit).all()
            return [r.to_dict() for r in records]
