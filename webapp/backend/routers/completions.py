from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Completion, ScheduleAssignment
from schemas import CompletionCreate, CompletionOut
from category_rotations import get_rotations_for_category

router = APIRouter()


@router.get("/resident/{resident_id}", response_model=list[CompletionOut])
def list_completions(resident_id: int, db: Session = Depends(get_db)):
    return [CompletionOut.model_validate(c) for c in db.query(Completion).filter(Completion.resident_id == resident_id).all()]


@router.post("/", response_model=CompletionOut)
def upsert_completion(data: CompletionCreate, db: Session = Depends(get_db)):
    if data.year_id is not None:
        rotations = get_rotations_for_category(data.category)
        if rotations:
            deleted = db.query(ScheduleAssignment).filter(
                ScheduleAssignment.resident_id == data.resident_id,
                ScheduleAssignment.year_id == data.year_id,
                ScheduleAssignment.rotation_code.in_(rotations),
            ).delete(synchronize_session=False)
            db.flush()
    payload = {k: v for k, v in data.model_dump().items() if k != "year_id"}
    existing = db.query(Completion).filter(
        Completion.resident_id == data.resident_id,
        Completion.category == data.category,
    ).first()
    if existing:
        existing.completed_weeks = data.completed_weeks
        existing.source = data.source
        db.commit()
        db.refresh(existing)
        return CompletionOut.model_validate(existing)
    c = Completion(**payload)
    db.add(c)
    db.commit()
    db.refresh(c)
    return CompletionOut.model_validate(c)
