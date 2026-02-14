from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import (
    Year, Cohort, Resident, Week, CoverageRule,
    ScheduleAssignment, ScheduleBackup, VacationRequest, Completion,
)

router = APIRouter()


class YearCreate(BaseModel):
    name: str
    start_date: str = ""


@router.get("/")
def list_years(db: Session = Depends(get_db)):
    return db.query(Year).all()


@router.get("/{year_id}")
def get_year(year_id: int, db: Session = Depends(get_db)):
    return db.query(Year).filter(Year.id == year_id).first()


@router.post("/")
def create_year(data: YearCreate, db: Session = Depends(get_db)):
    existing = db.query(Year).filter(Year.name == data.name).first()
    if existing:
        raise HTTPException(400, f"Year {data.name} already exists")
    start = data.start_date or f"{data.name.split('-')[0]}-07-01"
    y = Year(name=data.name, start_date=start)
    db.add(y)
    db.commit()
    db.refresh(y)
    for i in range(1, 6):
        db.add(Cohort(year_id=y.id, name=f"Cohort {i}", clinic_weeks=[], target_intern_count=2))
    db.commit()
    db.refresh(y)
    return y


@router.delete("/{year_id}")
def delete_year(year_id: int, db: Session = Depends(get_db)):
    """Delete a year and all its data (residents, cohorts, schedule, backups, vacation requests, etc.)."""
    y = db.query(Year).filter(Year.id == year_id).first()
    if not y:
        raise HTTPException(404, "Year not found")
    resident_ids = [r.id for r in db.query(Resident).filter(Resident.year_id == year_id).all()]
    db.query(Resident).filter(Resident.prior_resident_id.in_(resident_ids)).update(
        {Resident.prior_resident_id: None}, synchronize_session=False
    )
    db.query(ScheduleAssignment).filter(ScheduleAssignment.year_id == year_id).delete()
    db.query(ScheduleBackup).filter(ScheduleBackup.year_id == year_id).delete()
    db.query(VacationRequest).filter(VacationRequest.year_id == year_id).delete()
    for rid in resident_ids:
        db.query(Completion).filter(Completion.resident_id == rid).delete()
    db.query(Resident).filter(Resident.year_id == year_id).delete()
    db.query(Cohort).filter(Cohort.year_id == year_id).delete()
    db.query(Week).filter(Week.year_id == year_id).delete()
    db.query(CoverageRule).filter(CoverageRule.year_id == year_id).delete()
    db.delete(y)
    db.commit()
    return {"ok": True, "deleted": y.name}
