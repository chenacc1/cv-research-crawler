"""Author and PaperAuthor ORM models."""

import uuid

from sqlalchemy import Column, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Author(Base):
    __tablename__ = "author"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(256), nullable=False, unique=True)
    affiliation = Column(Text, nullable=True)

    papers = relationship(
        "PaperAuthor",
        back_populates="author",
        cascade="all, delete-orphan",
    )


class PaperAuthor(Base):
    __tablename__ = "paper_author"

    paper_id = Column(
        String(36),
        ForeignKey("paper.id", ondelete="CASCADE"),
        primary_key=True,
    )
    author_id = Column(
        String(36),
        ForeignKey("author.id", ondelete="CASCADE"),
        primary_key=True,
    )
    author_order = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("paper_id", "author_id", name="uq_paper_author"),
        Index("ix_paper_author_author", "author_id"),
    )

    paper = relationship("Paper", back_populates="authors")
    author = relationship("Author", back_populates="papers")
