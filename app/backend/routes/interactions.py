from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import crud, schemas
from ..db.database import get_db


router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("", response_model=schemas.Interaction)
def create_interaction(
    interaction: schemas.InteractionCreate,
    db: Session = Depends(get_db),
):
    return crud.create_interaction(db, interaction)
