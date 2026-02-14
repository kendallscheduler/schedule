from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Requirement, Resident, ScheduleAssignment
from schemas import RequirementCreate, RequirementOut, RequirementUpdate
from category_rotations import get_rotations_for_category

router = APIRouter()

# Format: (pgy, track, category, weeks). track=None = applies to all; track="anesthesia" = anesthesia TY only.
STANDARD_REQS = [
    # Categorical PGY1 (Total 52)
    ("PGY1", None, "FLOORS", 20), 
    ("PGY1", None, "ICU", 8), 
    ("PGY1", None, "CLINIC", 10), 
    ("PGY1", None, "VACATION", 4), 
    ("PGY1", None, "ELECTIVE", 10),
    ("PGY1", None, "CARDIO", 0), ("PGY1", None, "ID", 0), ("PGY1", None, "ED", 0), ("PGY1", None, "NEURO", 0), ("PGY1", None, "GERIATRICS", 0),
    
    # Categorical PGY2 (Total 52)
    ("PGY2", None, "FLOORS", 16), 
    ("PGY2", None, "ICU", 8), 
    ("PGY2", None, "CLINIC", 10), 
    ("PGY2", None, "VACATION", 4), 
    ("PGY2", None, "ELECTIVE", 14), 
    ("PGY2", None, "CARDIO", 0), ("PGY2", None, "ID", 0), ("PGY2", None, "ED", 0), ("PGY2", None, "NEURO", 0), ("PGY2", None, "GERIATRICS", 0),
    
    # Categorical PGY3 (Total 52)
    ("PGY3", None, "FLOORS", 8), 
    ("PGY3", None, "ICU", 4), 
    ("PGY3", None, "CLINIC", 14), 
    ("PGY3", None, "VACATION", 4),
    ("PGY3", None, "ELECTIVE", 6),
    ("PGY3", None, "CARDIO", 4), ("PGY3", None, "ID", 4), ("PGY3", None, "ED", 4), ("PGY3", None, "NEURO", 2), ("PGY3", None, "GERIATRICS", 2),

    # TY Residents (Shared core for both General/Neuro and Anesthesia)
    # 24 Floors (20 day / 4 night), 4 ICU (2 day / 2 night), 4 ED, 4 Gen Surg, 4 Clinic, 8 Elective, 4 Vac
    ("TY", None, "FLOORS", 24), 
    ("TY", None, "ICU", 4), 
    ("TY", None, "ED", 4),
    ("TY", None, "GEN SURG", 4),
    ("TY", None, "CLINIC", 4),
    ("TY", None, "VACATION", 4),
    ("TY", None, "ELECTIVE", 8),
]

# Core Electives are tracked cumulatively over 3 years for Categorical IM residents.
CUMULATIVE_CATEGORIES = {"CARDIO", "ID", "NEURO", "ED", "GERIATRICS"}
# Graduation targets for cumulative categories
CORE_MINS = {
    "CARDIO": 4,   # 4 weeks Cardiology
    "NEURO": 2,    # 2 weeks Neurology
    "ID": 4,       # 4 weeks Infectious Disease
    "GERIATRICS": 2, # 2 weeks Geriatrics
    "ED": 4,       # 4 weeks Emergency Dept
}


@router.get("/", response_model=list[RequirementOut])
def list_requirements(pgy: str = None, db: Session = Depends(get_db)):
    q = db.query(Requirement)
    if pgy:
        q = q.filter(Requirement.pgy == pgy)
    return [RequirementOut.model_validate(r) for r in q.all()]


@router.post("/", response_model=RequirementOut)
def create_requirement(data: RequirementCreate, db: Session = Depends(get_db)):
    r = Requirement(**data.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return RequirementOut.model_validate(r)


@router.post("/sync")
def sync_requirements(db: Session = Depends(get_db)):
    """Reset requirements to standard spec. Track-specific (e.g. anesthesia TY)."""
    std_set = {(pgy, track or "", cat) for pgy, track, cat, _ in STANDARD_REQS}
    for r in db.query(Requirement).all():
        key = (r.pgy, (r.track or ""), r.category)
        if key not in std_set:
            db.delete(r)
    for pgy, track, cat, weeks in STANDARD_REQS:
        q = db.query(Requirement).filter(Requirement.pgy == pgy, Requirement.category == cat)
        if track is None:
            q = q.filter(Requirement.track.is_(None))
        else:
            q = q.filter(Requirement.track == track)
        r = q.first()
        if r:
            r.required_weeks = weeks
        else:
            db.add(Requirement(pgy=pgy, track=track, category=cat, required_weeks=weeks))
    db.commit()
    count = db.query(Requirement).count()
    return {"ok": True, "total_requirements": count}


def _clear_schedule_for_category(db: Session, category: str, pgy: str, track: Optional[str]) -> int:
    """Clear schedule assignments that count toward this category for matching residents. Returns count cleared."""
    rotations = get_rotations_for_category(category)
    if not rotations:
        return 0
    year_ids = [row[0] for row in db.query(ScheduleAssignment.year_id).distinct().all()]
    cleared = 0
    for year_id in year_ids:
        residents = db.query(Resident).filter(
            Resident.year_id == year_id,
            Resident.pgy == pgy,
        )
        if track:
            residents = residents.filter(Resident.track == track)
        else:
            residents = residents.filter(Resident.track.is_(None))
        resident_ids = [res.id for res in residents.all()]
        for a in db.query(ScheduleAssignment).filter(
            ScheduleAssignment.year_id == year_id,
            ScheduleAssignment.resident_id.in_(resident_ids),
            ScheduleAssignment.rotation_code.in_(rotations),
        ).all():
            db.delete(a)
            cleared += 1
    return cleared


@router.patch("/{req_id}", response_model=RequirementOut)
def update_requirement(req_id: int, data: RequirementUpdate, db: Session = Depends(get_db)):
    r = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not r:
        raise HTTPException(404, "Requirement not found")
    if data.required_weeks is not None:
        if data.required_weeks == 0:
            _clear_schedule_for_category(db, r.category, r.pgy, r.track)
        r.required_weeks = data.required_weeks
    db.commit()
    db.refresh(r)
    return RequirementOut.model_validate(r)


@router.delete("/{req_id}")
def delete_requirement(req_id: int, db: Session = Depends(get_db)):
    r = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not r:
        raise HTTPException(404, "Requirement not found")
    _clear_schedule_for_category(db, r.category, r.pgy, r.track)
    db.delete(r)
    db.commit()
    return {"ok": True}
