from fastapi import APIRouter


router = APIRouter(tags=["system"])


@router.get("/")
def read_root():
    return {"message": "Bandit Backend API"}


@router.get("/health")
def health_check():
    return {"status": "ok"}
