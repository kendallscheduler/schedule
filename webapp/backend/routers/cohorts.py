from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Cohort

router = APIRouter()


@router.get("/")
def list_cohorts(year_id: int = None, db: Session = Depends(get_db)):
    q = db.query(Cohort)
    if year_id:
        q = q.filter(Cohort.year_id == year_id)
    return q.all()
