from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    ForeignKey,
    DateTime
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from Database.database import Base


"""
In your case:

Carousel = parent
Alternative = child

If an Alternative does not belong to any Carousel anymore, it becomes an orphan.
"""

class Carousel(Base):
    __tablename__ = "carousels"

    carousel_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    total_alternatives = Column(Integer, nullable=False)
    visible_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    alternatives = relationship(
        "Alternative",
        back_populates="carousel",
        cascade="all, delete-orphan" #
    )
    events = relationship(
        "InteractionEvent",
        back_populates="carousel",
        cascade="all, delete-orphan"
    )


class Alternative(Base):
    __tablename__ = "alternatives"

    alt_id = Column(Integer, primary_key=True, autoincrement=True)
    carousel_id = Column(
        Integer,
        ForeignKey("carousels.carousel_id", ondelete="CASCADE"),
        nullable=False
    )
    title = Column(String(255), nullable=False)
    alpha = Column(Float, default=1, nullable=False)
    beta = Column(Float, default=1, nullable=False)
    impressions = Column(Integer, default=0, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    carousel = relationship("Carousel", back_populates="alternatives")


class InteractionEvent(Base):
    __tablename__ = "interaction_events"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    carousel_id = Column(
        Integer,
        ForeignKey("carousels.carousel_id", ondelete="CASCADE"),
        nullable=False
    )
    round_number = Column(Integer, nullable=False)
    clicked_alt_id = Column(
        Integer,
        ForeignKey("alternatives.alt_id", ondelete="SET NULL"),
        nullable=True
    )
    reward = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    carousel = relationship("Carousel", back_populates="events")


class EventDisplayedAlternatives(Base):
    __tablename__ = "event_displayed_alternatives"

    event_id = Column(Integer, ForeignKey("interaction_events.event_id", ondelete="CASCADE"), primary_key=True)
    alt_id = Column(Integer, ForeignKey("alternatives.alt_id", ondelete="CASCADE"), primary_key=True)
    slot_position = Column(Integer, nullable=False)
    was_clicked = Column(Boolean, default=False, nullable=False)