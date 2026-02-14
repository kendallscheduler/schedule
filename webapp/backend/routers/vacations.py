from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import VacationRequest
from schemas import VacationRequestCreate, VacationRequestOut, VacationRequestsUpsert

router = APIRouter()


@router.get("/", response_model=list[VacationRequestOut])
def list_vacations(year_id: int = None, db: Session = Depends(get_db)):
    q = db.query(VacationRequest)
    if year_id:
        q = q.filter(VacationRequest.year_id == year_id)
    return [VacationRequestOut.model_validate(v) for v in q.all()]


@router.get("/resident/{resident_id}", response_model=dict)
def get_resident_vacation_requests(resident_id: int, year_id: int, db: Session = Depends(get_db)):
    """Get vacation requests for a resident in a given year, structured as Block A/B options."""
    rows = db.query(VacationRequest).filter(
        VacationRequest.resident_id == resident_id,
        VacationRequest.year_id == year_id,
    ).all()
    out = {"block_a_option1_start": None, "block_a_option2_start": None, "block_b_option1_start": None, "block_b_option2_start": None}
    for v in rows:
        if v.block == 1:
            if v.option == 1:
                out["block_a_option1_start"] = v.start_week
            else:
                out["block_a_option2_start"] = v.start_week
        else:
            if v.option == 1:
                out["block_b_option1_start"] = v.start_week
            else:
                out["block_b_option2_start"] = v.start_week
    return out


@router.post("/resident/upsert", response_model=dict)
def upsert_resident_vacation_requests(data: VacationRequestsUpsert, db: Session = Depends(get_db)):
    """Upsert vacation requests for a resident. Block A and B each have 2 date options."""
    db.query(VacationRequest).filter(
        VacationRequest.resident_id == data.resident_id,
        VacationRequest.year_id == data.year_id,
    ).delete()
    created = []
    for block, opt, start in [
        (1, 1, data.block_a_option1_start),
        (1, 2, data.block_a_option2_start),
        (2, 1, data.block_b_option1_start),
        (2, 2, data.block_b_option2_start),
    ]:
        if start is not None and 1 <= start <= 52:
            v = VacationRequest(
                resident_id=data.resident_id,
                year_id=data.year_id,
                block=block,
                option=opt,
                start_week=start,
                length_weeks=2,
                hard_lock=False,
            )
            db.add(v)
            created.append(v)
    db.commit()
    return {"ok": True, "created": len(created)}


@router.post("/", response_model=VacationRequestOut)
def create_vacation(data: VacationRequestCreate, db: Session = Depends(get_db)):
    v = VacationRequest(**data.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return VacationRequestOut.model_validate(v)


@router.delete("/{vac_id}")
def delete_vacation(vac_id: int, db: Session = Depends(get_db)):
    v = db.query(VacationRequest).filter(VacationRequest.id == vac_id).first()
    if not v:
        raise HTTPException(404, "Vacation request not found")
    db.delete(v)
    db.commit()
    return {"ok": True}
