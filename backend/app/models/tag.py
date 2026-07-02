"""UserTag, PaperTag, and RepoTag ORM models."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class UserTag(Base):
    __tablename__ = "user_tag"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(64), nullable=False, unique=True)
    color = Column(String(7), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    papers = relationship(
        "PaperTag",
        back_populates="tag",
        cascade="all, delete-orphan",
    )
    repos = relationship(
        "RepoTag",
        back_populates="tag",
        cascade="all, delete-orphan",
    )


class PaperTag(Base):
    __tablename__ = "paper_tag"

    paper_id = Column(
        String(36),
        ForeignKey("paper.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id = Column(
        String(36),
        ForeignKey("user_tag.id", ondelete="CASCADE"),
        primary_key=True,
    )

    __table_args__ = (
        UniqueConstraint("paper_id", "tag_id", name="uq_paper_tag"),
    )

    paper = relationship("Paper", back_populates="tags")
    tag = relationship("UserTag", back_populates="papers")


class RepoTag(Base):
    __tablename__ = "repo_tag"

    repo_id = Column(
        String(36),
        ForeignKey("github_repo.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id = Column(
        String(36),
        ForeignKey("user_tag.id", ondelete="CASCADE"),
        primary_key=True,
    )

    __table_args__ = (
        UniqueConstraint("repo_id", "tag_id", name="uq_repo_tag"),
    )

    repo = relationship("GitHubRepo", back_populates="tags")
    tag = relationship("UserTag", back_populates="repos")
