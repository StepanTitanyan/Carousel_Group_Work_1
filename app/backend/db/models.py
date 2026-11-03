from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from .database import Base

class Carousel(Base):
    __tablename__ = "carousels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    total_alternatives = Column(Integer, nullable=False)
    visible_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    round_number = Column(Integer, default=1)

    alternatives = relationship("Alternative", back_populates="carousel", cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="carousel", cascade="all, delete-orphan")

class Alternative(Base):
    __tablename__ = "alternatives"

    id = Column(Integer, primary_key=True, index=True)
    carousel_id = Column(UUID(as_uuid=True), ForeignKey("carousels.id"), nullable=False)
    alt_id = Column(Integer, nullable=False)  # Position within carousel
    title = Column(String, nullable=False)
    alpha = Column(Integer, default=1)
    beta = Column(Integer, default=1)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)

    carousel = relationship("Carousel", back_populates="alternatives")

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    carousel_id = Column(UUID(as_uuid=True), ForeignKey("carousels.id"), nullable=False)
    round = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    displayed = Column(JSON, nullable=False)  # List of alt_ids displayed
    clicked = Column(Integer, nullable=True)  # alt_id clicked, or None
    reward = Column(Integer, nullable=False)  # 0 or 1

    carousel = relationship("Carousel", back_populates="interactions")