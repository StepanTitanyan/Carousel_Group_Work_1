from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class AlternativeBase(BaseModel):
    alt_id: int
    title: str
    alpha: int = 1
    beta: int = 1
    impressions: int = 0
    clicks: int = 0

class Alternative(AlternativeBase):
    id: int
    carousel_id: UUID

    class Config:
        from_attributes = True

class InteractionBase(BaseModel):
    round: int
    displayed: List[int]
    clicked: Optional[int] = None
    reward: int

class Interaction(InteractionBase):
    id: int
    carousel_id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True

class CarouselBase(BaseModel):
    name: str
    total_alternatives: int
    visible_count: int

class CarouselCreate(CarouselBase):
    pass

class Carousel(CarouselBase):
    id: UUID
    created_at: datetime
    round_number: int
    alternatives: List[Alternative] = []
    interactions: List[Interaction] = []

    class Config:
        from_attributes = True

class CarouselUpdate(BaseModel):
    round_number: Optional[int] = None
    alternatives: Optional[List[AlternativeBase]] = None

class InteractionCreate(BaseModel):
    carousel_id: UUID
    round: int
    displayed: List[int]
    clicked: Optional[int] = None
    reward: int