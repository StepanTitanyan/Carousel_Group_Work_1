from . import models
from sqlalchemy.orm import Session
from . import schemas
from uuid import UUID

def get_carousels(db: Session):
    return db.query(models.Carousel).all()

def get_carousel(db: Session, carousel_id: UUID):
    return db.query(models.Carousel).filter(models.Carousel.id == carousel_id).first()

def create_carousel(db: Session, carousel: schemas.CarouselCreate):
    db_carousel = models.Carousel(
        name=carousel.name,
        total_alternatives=carousel.total_alternatives,
        visible_count=carousel.visible_count
    )
    db.add(db_carousel)
    db.commit()
    db.refresh(db_carousel)
    
    # Create alternatives
    for i in range(1, carousel.total_alternatives + 1):
        alt = models.Alternative(
            carousel_id=db_carousel.id,
            alt_id=i,
            title=f"Alternative {i}"
        )
        db.add(alt)
    
    db.commit()
    db.refresh(db_carousel)
    return db_carousel

def update_carousel(db: Session, carousel_id: UUID, carousel_update: schemas.CarouselUpdate):
    db_carousel = db.query(models.Carousel).filter(models.Carousel.id == carousel_id).first()
    if db_carousel:
        if carousel_update.round_number is not None:
            db_carousel.round_number = carousel_update.round_number
        if carousel_update.alternatives:
            # Update alternatives
            for alt_update in carousel_update.alternatives:
                alt = db.query(models.Alternative).filter(
                    models.Alternative.carousel_id == carousel_id,
                    models.Alternative.alt_id == alt_update.alt_id
                ).first()
                if alt:
                    alt.alpha = alt_update.alpha
                    alt.beta = alt_update.beta
                    alt.impressions = alt_update.impressions
                    alt.clicks = alt_update.clicks
        db.commit()
        db.refresh(db_carousel)
    return db_carousel

def create_interaction(db: Session, interaction: schemas.InteractionCreate):
    db_interaction = models.Interaction(
        carousel_id=interaction.carousel_id,
        round=interaction.round,
        displayed=interaction.displayed,
        clicked=interaction.clicked,
        reward=interaction.reward
    )
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

def reset_carousel(db: Session, carousel_id: UUID):
    db_carousel = db.query(models.Carousel).filter(models.Carousel.id == carousel_id).first()
    if db_carousel:
        db_carousel.round_number = 1
        # Reset alternatives
        db.query(models.Alternative).filter(models.Alternative.carousel_id == carousel_id).update({
            "alpha": 1,
            "beta": 1,
            "impressions": 0,
            "clicks": 0
        })
        # Delete interactions
        db.query(models.Interaction).filter(models.Interaction.carousel_id == carousel_id).delete()
        db.commit()
        db.refresh(db_carousel)
    return db_carousel

def delete_carousel(db: Session, carousel_id: UUID):
    db_carousel = db.query(models.Carousel).filter(models.Carousel.id == carousel_id).first()
    if db_carousel:
        db.delete(db_carousel)
        db.commit()
    return db_carousel