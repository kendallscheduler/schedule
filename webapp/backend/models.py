"""SQLAlchemy models for the scheduling DB."""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, ForeignKey, JSON, DateTime, Text,
)
from sqlalchemy.orm import relationship

from database import Base


class Year(Base):
    __tablename__ = "years"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)  # e.g. "2025-2026"
    start_date = Column(String(20))  # e.g. "2025-07-01"


class Resident(Base):
    __tablename__ = "residents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    pgy = Column(String(10), nullable=False)  # PGY1, PGY2, PGY3, TY
    cohort_id = Column(Integer, ForeignKey("cohorts.id"), nullable=True)
    prior_resident_id = Column(Integer, ForeignKey("residents.id"), nullable=True)  # prior year when rolled over
    track = Column(String(50), nullable=True)  # anesthesia, etc.
    year_id = Column(Integer, ForeignKey("years.id"), nullable=False)
    constraints_json = Column(JSON, default=dict)  # {"no_cardio_before_week": 7}
    is_placeholder = Column(Boolean, default=False)  # Intern 01, TY 01, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    cohort = relationship("Cohort", back_populates="residents")
    year = relationship("Year")
    completions = relationship("Completion", back_populates="resident")
    vacation_requests = relationship("VacationRequest", back_populates="resident")
    schedule_assignments = relationship("ScheduleAssignment", back_populates="resident")

    @property
    def is_senior(self) -> bool:
        return self.pgy in ("PGY2", "PGY3")

    @property
    def is_intern(self) -> bool:
        return self.pgy in ("PGY1", "TY")

    @property
    def cohort_name(self) -> Optional[str]:
        return self.cohort.name if self.cohort else None


class Cohort(Base):
    __tablename__ = "cohorts"
    id = Column(Integer, primary_key=True, index=True)
    year_id = Column(Integer, ForeignKey("years.id"), nullable=False)
    name = Column(String(50), nullable=False)  # Cohort 1, Cohort 2, ...
    clinic_weeks = Column(JSON, default=list)  # [1,6,11,16,...]
    target_intern_count = Column(Integer, default=2)

    residents = relationship("Resident", back_populates="cohort")
    year = relationship("Year")


class Requirement(Base):
    __tablename__ = "requirements"
    id = Column(Integer, primary_key=True, index=True)
    pgy = Column(String(10), nullable=False)
    track = Column(String(50), nullable=True)  # anesthesia, neurology; null = applies to all
    category = Column(String(50), nullable=False, index=True)
    required_weeks = Column(Integer, nullable=False, default=0)
    min_weeks = Column(Integer, nullable=True)
    max_weeks = Column(Integer, nullable=True)
    counts_as = Column(JSON, default=list)  # rotation codes that fulfill this

    __table_args__ = ({"sqlite_autoincrement": True},)


class Completion(Base):
    __tablename__ = "completions"
    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("residents.id"), nullable=False)
    category = Column(String(50), nullable=False)
    completed_weeks = Column(Integer, nullable=False, default=0)
    source = Column(String(20), default="manual")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resident = relationship("Resident", back_populates="completions")


class VacationRequest(Base):
    __tablename__ = "vacation_requests"
    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("residents.id"), nullable=False)
    year_id = Column(Integer, ForeignKey("years.id"), nullable=False)
    block = Column(Integer, nullable=False)  # 1 = Block A, 2 = Block B
    option = Column(Integer, nullable=False, default=1)  # 1 or 2 = which date choice for that block
    start_week = Column(Integer, nullable=False)
    length_weeks = Column(Integer, nullable=False, default=2)
    priority = Column(Integer, default=3)  # 1-5
    hard_lock = Column(Boolean, default=False)  # if True, force these weeks (legacy)

    resident = relationship("Resident", back_populates="vacation_requests")


class Week(Base):
    __tablename__ = "weeks"
    id = Column(Integer, primary_key=True, index=True)
    year_id = Column(Integer, ForeignKey("years.id"), nullable=False)
    week_number = Column(Integer, nullable=False)
    start_date = Column(String(20))
    end_date = Column(String(20))
    month_label = Column(String(20))  # July, August, etc.

    year = relationship("Year")


class Rotation(Base):
    __tablename__ = "rotations"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    type = Column(String(20))  # floor, icu, night, clinic, elective
    is_night = Column(Boolean, default=False)
    staffing_role_allowed = Column(String(20), default="both")  # senior, intern, both
    counts_toward_category = Column(String(50))  # FLOORS, ICU, CLINIC, etc.


class CoverageRule(Base):
    __tablename__ = "coverage_rules"
    id = Column(Integer, primary_key=True, index=True)
    year_id = Column(Integer, ForeignKey("years.id"), nullable=False)
    week_scope = Column(String(20), default="all")  # all or specific
    pool = Column(String(50), nullable=False)
    required_units_per_week = Column(Integer, nullable=False)
    seniors_per_unit = Column(Integer, default=0)
    interns_per_unit = Column(Integer, default=0)
    optional = Column(Boolean, default=False)


class ScheduleAssignment(Base):
    __tablename__ = "schedule_assignments"
    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("residents.id"), nullable=False)
    year_id = Column(Integer, ForeignKey("years.id"), nullable=False)
    week_number = Column(Integer, nullable=False)
    rotation_code = Column(String(50), nullable=False)

    resident = relationship("Resident", back_populates="schedule_assignments")


class ScheduleBackup(Base):
    """Backup of schedule assignments before clear. JSON: {resident_id: {week: rotation_code}}."""
    __tablename__ = "schedule_backups"
    id = Column(Integer, primary_key=True, index=True)
    year_id = Column(Integer, ForeignKey("years.id"), nullable=False)
    description = Column(String(200), nullable=False)
    assignments_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
