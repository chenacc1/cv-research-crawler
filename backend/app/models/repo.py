"""GitHubRepo ORM model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.database import Base


class GitHubRepo(Base):
    __tablename__ = "github_repo"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(256), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    url = Column(String(2048), nullable=False)
    stars = Column(Integer, default=0)
    previous_stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    language = Column(String(64), nullable=True)
    topics = Column(JSON, nullable=True)
    pushed_at = Column(DateTime(timezone=True), nullable=True)
    crawled_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    last_crawled_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    summary_cn = Column(Text, nullable=True)
    summary_en = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("full_name", name="uq_repo_full_name"),
        Index("ix_repo_stars", stars.desc()),
        Index("ix_repo_pushed_at", pushed_at.desc()),
        Index("ix_repo_language", "language"),
    )

    tags = relationship(
        "RepoTag",
        back_populates="repo",
        cascade="all, delete-orphan",
    )
