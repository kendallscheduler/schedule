from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Rotation

router = APIRouter()


@router.get("/")
def list_rotations(db: Session = Depends(get_db)):
    return db.query(Rotation).all()
