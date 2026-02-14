from database import SessionLocal
from models import ScheduleAssignment, Resident, Rotation
import json

db = SessionLocal()
residents = {r.id: r for r in db.query(Resident).all()}
rotations = {rot.code: rot for rot in db.query(Rotation).all()}

# Floor codes: A, B, C, D
FLOOR_CODES = ["A", "B", "C", "D"]

assignments = db.query(ScheduleAssignment).all()
weeks = {}
for a in assignments:
    weeks.setdefault(a.week_number, {}).setdefault(a.rotation_code, []).append(a.resident_id)

issues = []
for w_num in sorted(weeks.keys()):
    w_data = weeks[w_num]
    for code in FLOOR_CODES:
        residents_on_floor = w_data.get(code, [])
        seniors = [rid for rid in residents_on_floor if residents[rid].is_senior]
        interns = [rid for rid in residents_on_floor if residents[rid].is_intern]
        
        if len(seniors) != 1 or len(interns) != 2:
            issues.append(f"Week {w_num}, Team {code}: Seniors={len(seniors)} ({seniors}), Interns={len(interns)} ({interns})")

print(f"Total issues found: {len(issues)}")
for issue in issues[:20]:
    print(issue)
if len(issues) > 20:
    print("...")

# Also check ICU
print("\nChecking ICU (Day):")
for w_num in sorted(weeks.keys()):
    w_data = weeks[w_num]
    icu_residents = w_data.get("ICU", []) + w_data.get("ICU E", [])
    seniors = [rid for rid in icu_residents if residents[rid].is_senior]
    interns = [rid for rid in icu_residents if residents[rid].is_intern]
    if len(seniors) != 2 or len(interns) != 2:
         print(f"Week {w_num}, ICU: Seniors={len(seniors)}, Interns={len(interns)}")

db.close()
