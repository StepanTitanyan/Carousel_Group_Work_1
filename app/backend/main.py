from fastapi import FastAPI

from .db import models
from .db.database import engine
from .routes import carousels_router, interactions_router, system_router


models.Base.metadata.create_all(bind=engine)


def create_app() -> FastAPI:
    app = FastAPI(title="Bandit Backend API")
    app.include_router(system_router)
    app.include_router(carousels_router)
    app.include_router(interactions_router)
    return app


app = create_app()
