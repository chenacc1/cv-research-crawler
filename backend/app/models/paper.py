"""Paper ORM model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Paper(Base):
    __tablename__ = "paper"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(1024), nullable=False)
    title_normalized = Column(String(1024), nullable=False, index=True)
    abstract = Column(Text, nullable=True)
    url = Column(String(2048), nullable=False)
    pdf_url = Column(String(2048), nullable=True)
    code_url = Column(String(2048), nullable=True)
    source = Column(String(32), nullable=False, index=True)
    source_id = Column(String(128), nullable=False)
    venue = Column(String(256), nullable=True)
    published_date = Column(Date, nullable=True)
    crawled_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    merged_into_id = Column(
        String(36),
        ForeignKey("paper.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    summary_cn = Column(Text, nullable=True)
    summary_en = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_paper_source_id"),
        Index("ix_paper_published_date", published_date.desc()),
        Index("ix_paper_crawled_at", "crawled_at"),
    )

    # Relationships
    authors = relationship(
        "PaperAuthor",
        back_populates="paper",
        cascade="all, delete-orphan",
    )
    categories = relationship(
        "PaperCategory",
        back_populates="paper",
        cascade="all, delete-orphan",
    )
    tags = relationship(
        "PaperTag",
        back_populates="paper",
        cascade="all, delete-orphan",
    )
    merged_into = relationship("Paper", remote_side=[id], backref="versions")
