#!/usr/bin/env python3
"""Seed database with weeks, rotations, coverage rules, requirements."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import engine, SessionLocal, Base
from models import Year, Week, Rotation, CoverageRule, Requirement, Cohort

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Year
year = db.query(Year).filter(Year.name == "2025-2026").first()
if not year:
    year = Year(name="2025-2026", start_date="2025-07-01")
    db.add(year)
    db.commit()
    db.refresh(year)

# Weeks (academic year 07/01 - 06/30)
date_ranges = [
    ("07/01", "07/06"), ("07/07", "07/13"), ("07/14", "07/20"), ("07/21", "07/27"), ("07/28", "08/03"),
    ("08/04", "08/10"), ("08/11", "08/17"), ("08/18", "08/24"), ("08/25", "08/31"), ("09/01", "09/07"),
    ("09/08", "09/14"), ("09/15", "09/21"), ("09/22", "09/28"), ("09/29", "10/05"), ("10/06", "10/12"),
    ("10/13", "10/19"), ("10/20", "10/26"), ("10/27", "11/02"), ("11/03", "11/09"), ("11/10", "11/16"),
    ("11/17", "11/23"), ("11/24", "11/30"), ("12/01", "12/07"), ("12/08", "12/14"), ("12/15", "12/21"),
    ("12/22", "12/28"), ("12/29", "01/04"), ("01/05", "01/11"), ("01/12", "01/18"), ("01/19", "01/25"),
    ("01/26", "02/01"), ("02/02", "02/08"), ("02/09", "02/15"), ("02/16", "02/22"), ("02/23", "03/01"),
    ("03/02", "03/08"), ("03/09", "03/15"), ("03/16", "03/22"), ("03/23", "03/29"), ("03/30", "04/05"),
    ("04/06", "04/12"), ("04/13", "04/19"), ("04/20", "04/26"), ("04/27", "05/03"), ("05/04", "05/10"),
    ("05/11", "05/17"), ("05/18", "05/24"), ("05/25", "05/31"), ("06/01", "06/07"), ("06/08", "06/14"),
    ("06/15", "06/21"), ("06/22", "06/30"),
]
months = ["July"]*5 + ["August"]*4 + ["September"]*4 + ["October"]*4 + ["November"]*4 + ["December"]*4 + ["January"]*4 + ["February"]*4 + ["March"]*4 + ["April"]*4 + ["May"]*4 + ["June"]*4
for i, ((s, e), m) in enumerate(zip(date_ranges, months)):
    w = db.query(Week).filter(Week.year_id == year.id, Week.week_number == i + 1).first()
    if not w:
        db.add(Week(year_id=year.id, week_number=i+1, start_date=s, end_date=e, month_label=m))
db.commit()

# Rotations
rotations = [
    ("A", "floor", False, "both", "FLOORS"),
    ("B", "floor", False, "both", "FLOORS"),
    ("C", "floor", False, "both", "FLOORS"),
    ("D", "floor", False, "both", "FLOORS"),
    ("G", "floor", False, "senior", "FLOORS"),
    ("ICU", "icu", False, "both", "ICU"),
    ("ICU E", "icu", False, "both", "ICU"),
    ("ICU N", "icu", True, "both", "ICU"),
    ("ICU H", "elective", False, "both", "ELECTIVE"),  # Placeholder: Christmas or New Year off
    ("NF", "night", True, "both", "NF"),
    ("SWING", "night", False, "senior", "SWING"),
    ("CLINIC", "clinic", False, "both", "CLINIC"),
    ("CLINIC *", "clinic", False, "both", "CLINIC"),
    ("ED", "elective", False, "both", "ED"),
    ("CARDIO", "elective", False, "both", "CARDIO"),
    ("CARDIO-RAM", "elective", False, "both", "CARDIO"),
    ("CARDIO-HCA", "elective", False, "both", "CARDIO"),
    ("ID", "elective", False, "both", "ID"),
    ("NEURO", "elective", False, "both", "NEURO"),
    ("VACATION", "elective", False, "both", "VACATION"),
    ("GERIATRICS", "elective", False, "both", "GERIATRICS"),
    ("PULMONOLOGY", "elective", False, "both", "PULMONOLOGY"),
    ("NEPHROLOGY", "elective", False, "both", "NEPHROLOGY"),
    ("PALLIATIVE", "elective", False, "both", "PALLIATIVE"),
    ("PAIN", "elective", False, "both", "PAIN"),
    ("RHEUMATOLOGY", "elective", False, "both", "RHEUMATOLOGY"),
    ("ENDOCRINOLOGY", "elective", False, "both", "ENDOCRINOLOGY"),
    ("TRAUMA", "elective", False, "both", "TRAUMA"),
    ("SICU", "elective", False, "both", "SICU"),
    ("PLASTIC", "elective", False, "both", "PLASTIC"),
    ("ELECTIVE", "elective", False, "both", "ELECTIVE"),
]
for code, t, night, role, cat in rotations:
    if not db.query(Rotation).filter(Rotation.code == code).first():
        db.add(Rotation(code=code, type=t, is_night=night, staffing_role_allowed=role, counts_toward_category=cat))
db.commit()

# Coverage rules
coverage = [
    ("FLOOR_A", 1, 1, 2, False),
    ("FLOOR_B", 1, 1, 2, False),
    ("FLOOR_C", 1, 1, 2, False),
    ("FLOOR_D", 1, 1, 2, False),
    ("ICU_DAY", 1, 2, 2, False),
    ("NF", 1, 1, 1, False),
    ("ICUN", 1, 1, 1, False),
    ("SWING", 1, 1, 0, False),
    ("TEAM_G", 0, 1, 0, True),
]
for pool, units, sr, ir, opt in coverage:
    if not db.query(CoverageRule).filter(CoverageRule.year_id == year.id, CoverageRule.pool == pool).first():
        db.add(CoverageRule(year_id=year.id, pool=pool, required_units_per_week=units, seniors_per_unit=sr, interns_per_unit=ir, optional=opt))
db.commit()

# Core requirements per year. (Min weeks)
# Tracks: TY:anesthesia for anesthesia residents.
# Core requirements per year. (Min weeks)
# Tracks: None=Categorical/General, 'anesthesia'=Anesthesia track.
db.query(Requirement).delete()

# Core requirements per year. (Min weeks)
# Tracks: None=Categorical/General, 'anesthesia'=Anesthesia track.
reqs = [
    # Categorical PGY1 (Total 52)
    ("PGY1", "FLOORS", 20, None), 
    ("PGY1", "ICU", 8, None), 
    ("PGY1", "CLINIC", 10, None), 
    ("PGY1", "VACATION", 4, None), 
    ("PGY1", "ELECTIVE", 10, None),
    ("PGY1", "CARDIO", 0, None), ("PGY1", "ID", 0, None), ("PGY1", "ED", 0, None), ("PGY1", "NEURO", 0, None), ("PGY1", "GERIATRICS", 0, None),
    
    # Categorical PGY2 (Total 52)
    ("PGY2", "FLOORS", 16, None), 
    ("PGY2", "ICU", 8, None), 
    ("PGY2", "CLINIC", 10, None), 
    ("PGY2", "VACATION", 4, None), 
    ("PGY2", "ELECTIVE", 14, None),
    ("PGY2", "CARDIO", 0, None), ("PGY2", "ID", 0, None), ("PGY2", "ED", 0, None), ("PGY2", "NEURO", 0, None), ("PGY2", "GERIATRICS", 0, None),
    
    # Categorical PGY3 (Total 52)
    ("PGY3", "FLOORS", 8, None), 
    ("PGY3", "ICU", 4, None), 
    ("PGY3", "CLINIC", 14, None), 
    ("PGY3", "VACATION", 4, None),
    ("PGY3", "ELECTIVE", 6, None),
    ("PGY3", "CARDIO", 4, None), ("PGY3", "ID", 4, None), ("PGY3", "ED", 4, None), ("PGY3", "NEURO", 2, None), ("PGY3", "GERIATRICS", 2, None),

    # TY Residents (Shared core)
    ("TY", "FLOORS", 24, None), 
    ("TY", "ICU", 4, None), 
    ("TY", "ED", 4, None),
    ("TY", "GEN SURG", 4, None),
    ("TY", "CLINIC", 4, None),
    ("TY", "VACATION", 4, None),
    ("TY", "ELECTIVE", 8, None),
]
for pgy, cat, weeks, track in reqs:
    db.add(Requirement(pgy=pgy, category=cat, required_weeks=weeks, track=track))
db.commit()

# Cohorts (4+1 clinic rhythm)
clinic_weeks = {
    "Cohort 1": [1, 6, 11, 16, 21, 28, 33, 38, 43, 48],
    "Cohort 2": [2, 7, 12, 17, 22, 29, 34, 39, 44, 49],
    "Cohort 3": [3, 8, 13, 18, 23, 30, 35, 40, 45, 50],
    "Cohort 4": [4, 9, 14, 19, 24, 31, 36, 41, 46],
    "Cohort 5": [5, 10, 15, 20, 25, 32, 37, 47, 52],
}
for i, (name, weeks) in enumerate(clinic_weeks.items(), 1):
    if not db.query(Cohort).filter(Cohort.year_id == year.id, Cohort.name == name).first():
        db.add(Cohort(year_id=year.id, name=name, clinic_weeks=weeks, target_intern_count=2))
db.commit()

print("Seeded: years, weeks, rotations, coverage_rules, requirements, cohorts")
db.close()
