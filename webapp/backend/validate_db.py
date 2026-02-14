from database import SessionLocal
from models import Resident, ScheduleAssignment, Year, Rotation, Cohort
import json

db = SessionLocal()
residents = {r.id: r for r in db.query(Resident).all()}
assignments = db.query(ScheduleAssignment).all()
weeks = {}
for a in assignments:
    weeks.setdefault(a.week_number, {}).setdefault(a.resident_id, a.rotation_code)

# Rotation codes
FLOOR_CODES = ["A", "B", "C", "D"]
ICU_CODES = ["ICU", "ICU E"]
ICUN_CODE = "ICU N"
NF_CODE = "NF"
SWING_CODE = "SWING"
G_CODE = "G"

violations = []

for w in range(1, 53):
    # Check each floor team
    for code in FLOOR_CODES:
        residents_on_team = [rid for rid, rot in weeks.get(w, {}).items() if rot == code]
        sr = [rid for rid in residents_on_team if residents[rid].is_senior]
        jr = [rid for rid in residents_on_team if residents[rid].is_intern]
        if len(sr) != 1:
            violations.append(f"Week {w}, Team {code}: seniors={len(sr)} (Expected 1)")
        if len(jr) != 2:
            violations.append(f"Week {w}, Team {code}: interns={len(jr)} (Expected 2)")
    
    # Check ICU
    residents_icu = [rid for rid, rot in weeks.get(w, {}).items() if rot in ICU_CODES]
    sr_icu = [rid for rid in residents_icu if residents[rid].is_senior]
    jr_icu = [rid for rid in residents_icu if residents[rid].is_intern]
    if len(sr_icu) != 2:
        violations.append(f"Week {w}, ICU: seniors={len(sr_icu)} (Expected 2)")
    if len(jr_icu) != 2:
        violations.append(f"Week {w}, ICU: interns={len(jr_icu)} (Expected 2)")

    # Check ICU N
    residents_icun = [rid for rid, rot in weeks.get(w, {}).items() if rot == ICUN_CODE]
    sr_icun = [rid for rid in residents_icun if residents[rid].is_senior]
    jr_icun = [rid for rid in residents_icun if residents[rid].is_intern]
    if len(sr_icun) != 1:
        violations.append(f"Week {w}, ICU N: seniors={len(sr_icun)} (Expected 1)")
    if len(jr_icun) != 1:
        violations.append(f"Week {w}, ICU N: interns={len(jr_icun)} (Expected 1)")

print(f"Total violations found: {len(violations)}")
for v in violations[:30]:
    print(v)
db.close()
