from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import crud, schemas
from ..db.database import get_db


router = APIRouter(prefix="/carousels", tags=["carousels"])


@router.get("", response_model=list[schemas.Carousel])
def read_carousels(db: Session = Depends(get_db)):
    return crud.get_carousels(db)


@router.get("/{carousel_id}", response_model=schemas.Carousel)
def read_carousel(carousel_id: UUID, db: Session = Depends(get_db)):
    db_carousel = crud.get_carousel(db, carousel_id)
    if db_carousel is None:
        raise HTTPException(status_code=404, detail="Carousel not found")
    return db_carousel


@router.post("", response_model=schemas.Carousel)
def create_carousel(
    carousel: schemas.CarouselCreate,
    db: Session = Depends(get_db),
):
    return crud.create_carousel(db, carousel)


@router.put("/{carousel_id}", response_model=schemas.Carousel)
def update_carousel(
    carousel_id: UUID,
    carousel_update: schemas.CarouselUpdate,
    db: Session = Depends(get_db),
):
    db_carousel = crud.update_carousel(db, carousel_id, carousel_update)
    if db_carousel is None:
        raise HTTPException(status_code=404, detail="Carousel not found")
    return db_carousel


@router.put("/{carousel_id}/reset", response_model=schemas.Carousel)
def reset_carousel(carousel_id: UUID, db: Session = Depends(get_db)):
    db_carousel = crud.reset_carousel(db, carousel_id)
    if db_carousel is None:
        raise HTTPException(status_code=404, detail="Carousel not found")
    return db_carousel


@router.delete("/{carousel_id}")
def delete_carousel(carousel_id: UUID, db: Session = Depends(get_db)):
    db_carousel = crud.delete_carousel(db, carousel_id)
    if db_carousel is None:
        raise HTTPException(status_code=404, detail="Carousel not found")
    return {"message": "Carousel deleted successfully"}
