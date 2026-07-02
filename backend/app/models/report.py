"""Report ORM model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, Date, DateTime, Index, Integer, String

from app.database import Base


class Report(Base):
    __tablename__ = "report"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String(16), nullable=False)
    date_range_start = Column(Date, nullable=False)
    date_range_end = Column(Date, nullable=False)
    file_path = Column(String(2048), nullable=False)
    paper_count = Column(Integer, default=0)
    repo_count = Column(Integer, default=0)
    delivery_status = Column(String(16), default="pending")
    generated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("ix_report_type_generated", type, generated_at.desc()),
    )
