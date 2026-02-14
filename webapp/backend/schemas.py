"""Pydantic schemas for API."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ResidentBase(BaseModel):
    name: str
    pgy: str
    cohort_id: Optional[int] = None
    track: Optional[str] = None
    constraints_json: Dict[str, Any] = {}


class ResidentCreate(ResidentBase):
    year_id: int


class ResidentUpdate(BaseModel):
    name: Optional[str] = None
    pgy: Optional[str] = None
    cohort_id: Optional[int] = None
    track: Optional[str] = None
    constraints_json: Optional[Dict[str, Any]] = None
    is_placeholder: Optional[bool] = None


class ResidentOut(ResidentBase):
    id: int
    year_id: int
    is_senior: bool
    is_intern: bool
    is_placeholder: bool = False
    cohort_name: Optional[str] = None

    class Config:
        from_attributes = True


class PasteScheduleRequest(BaseModel):
    year_id: int
    assignments: str  # Whitespace-separated rotation codes; may start with "Cohort N PGY-N Name"


class RequirementBase(BaseModel):
    pgy: str
    track: Optional[str] = None
    category: str
    required_weeks: int
    min_weeks: Optional[int] = None
    max_weeks: Optional[int] = None
    counts_as: List[str] = []


class RequirementCreate(RequirementBase):
    pass


class RequirementUpdate(BaseModel):
    required_weeks: Optional[int] = None


class RequirementOut(RequirementBase):
    id: int

    class Config:
        from_attributes = True


class CompletionBase(BaseModel):
    resident_id: int
    category: str
    completed_weeks: int
    source: str = "manual"
    year_id: Optional[int] = None  # If set, sync to schedule: clear assignments for this category


class CompletionCreate(CompletionBase):
    pass


class CompletionOut(CompletionBase):
    id: int

    class Config:
        from_attributes = True


class VacationRequestBase(BaseModel):
    resident_id: int
    year_id: int
    block: int
    option: int = 1  # 1 or 2 = which date choice for that block
    start_week: int
    length_weeks: int = 2
    priority: int = 3
    hard_lock: bool = False


class VacationRequestCreate(VacationRequestBase):
    pass


class VacationRequestOut(VacationRequestBase):
    id: int

    class Config:
        from_attributes = True


class VacationRequestsUpsert(BaseModel):
    """Upsert vacation requests for a resident. Block A = 2 options, Block B = 2 options."""
    resident_id: int
    year_id: int
    block_a_option1_start: Optional[int] = None  # week number
    block_a_option2_start: Optional[int] = None
    block_b_option1_start: Optional[int] = None
    block_b_option2_start: Optional[int] = None


class ScheduleAssignmentOut(BaseModel):
    resident_id: int
    week_number: int
    rotation_code: str


class UpdateAssignmentRequest(BaseModel):
    resident_id: int
    year_id: int
    week_number: int
    rotation_code: str = ""  # empty = clear cell


class GenerateScheduleRequest(BaseModel):
    year_id: int
    time_limit_seconds: int = 0  # 0 = unlimited; else seconds
    random_seed: Optional[int] = None


class GenerateScheduleResponse(BaseModel):
    success: bool
    status: str  # FEASIBLE, OPTIMAL, INFEASIBLE
    message: Optional[str] = None
    conflicts: List[str] = []
    assignment_count: int = 0


class ClearScheduleRequest(BaseModel):
    year_id: int
    resident_id: Optional[int] = None  # If set, clear only this resident; else clear all
    confirm_text: str  # Must be exactly "DELETE" to proceed


class ScheduleBackupOut(BaseModel):
    id: int
    year_id: int
    description: str
    created_at: str

    class Config:
        from_attributes = True
