"""Category and PaperCategory ORM models."""

import uuid

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Category(Base):
    __tablename__ = "category"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=False)
    source = Column(String(32), nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "name", name="uq_category_source_name"),
    )

    papers = relationship(
        "PaperCategory",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class PaperCategory(Base):
    __tablename__ = "paper_category"

    paper_id = Column(
        String(36),
        ForeignKey("paper.id", ondelete="CASCADE"),
        primary_key=True,
    )
    category_id = Column(
        String(36),
        ForeignKey("category.id", ondelete="CASCADE"),
        primary_key=True,
    )

    __table_args__ = (
        UniqueConstraint("paper_id", "category_id", name="uq_paper_category"),
    )

    paper = relationship("Paper", back_populates="categories")
    category = relationship("Category", back_populates="papers")
