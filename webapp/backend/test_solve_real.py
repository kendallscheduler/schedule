from database import SessionLocal
from models import Resident, Requirement, Completion, VacationRequest, Cohort, Year
from engine import solve
import json

db = SessionLocal()
year = db.query(Year).filter(Year.name == "2026-2027").first()

residents = db.query(Resident).filter(Resident.year_id == year.id).all()
residents_data = []
for r in residents:
    residents_data.append({
        "id": r.id, "name": r.name, "pgy": r.pgy, "track": r.track, "cohort_id": r.cohort_id,
        "is_ty": r.pgy == "TY", "is_intern": r.pgy in ("PGY1", "TY"), "is_senior": r.pgy in ("PGY2", "PGY3"),
        "constraints_json": r.constraints_json if r.constraints_json else {},
    })

completions = db.query(Completion).all()
completions_by_resident = {}
for c in completions:
    completions_by_resident.setdefault(c.resident_id, {})[c.category] = c.completed_weeks

cohorts = db.query(Cohort).filter(Cohort.year_id == year.id).all()
cohort_defs = []
for c in cohorts:
    weeks = json.loads(str(c.clinic_weeks)) if isinstance(c.clinic_weeks, str) else c.clinic_weeks
    cohort_defs.append({"cohort_id": c.id, "clinic_weeks": weeks or []})

reqs = db.query(Requirement).all()
requirements_by_pgy = {}
for r in reqs:
    key = f"{r.pgy}:{r.track or ''}"
    requirements_by_pgy.setdefault(key, []).append({
        "category": r.category, "required_weeks": r.required_weeks,
    })

assignments, status, conflicts = solve(
    residents=residents_data,
    requirements_by_pgy=requirements_by_pgy,
    completions_by_resident=completions_by_resident,
    vacation_requests=[],
    cohort_defs=cohort_defs,
    time_limit=300,
)

print(f"Status: {status}")
if assignments:
    # Verify vacation blocks are exactly 2+2
    print("\n=== VACATION BLOCK VERIFICATION ===")
    all_good = True
    for rid, weeks in assignments.items():
        res = next(r for r in residents_data if r["id"] == rid)
        vac_weeks = sorted([w for w, rot in weeks.items() if rot == "VACATION"])
        # Check for isolated weeks
        blocks = []
        current_block = []
        for w in vac_weeks:
            if current_block and w != current_block[-1] + 1:
                blocks.append(current_block)
                current_block = []
            current_block.append(w)
        if current_block:
            blocks.append(current_block)
        block_sizes = [len(b) for b in blocks]
        ok = all(s == 2 for s in block_sizes) and len(blocks) == 2
        if not ok:
            print(f"  FAIL {res['name']} ({res['pgy']}): blocks={block_sizes}, weeks={vac_weeks}")
            all_good = False
    if all_good:
        print("  ALL VACATIONS ARE CORRECT 2+2 BLOCKS ✓")
    
    # Show co-intern pairing
    print("\n=== CO-INTERN PAIRING ===")
    cohort_interns = {}
    for r in residents_data:
        if r["pgy"] in ("PGY1", "TY") and r.get("cohort_id"):
            cohort_interns.setdefault(r["cohort_id"], []).append(r)
    for cid, interns in sorted(cohort_interns.items()):
        if len(interns) >= 2:
            pairs = [(interns[i], interns[i+1]) for i in range(0, len(interns)-1, 2)]
            for a, b in pairs:
                shared = 0
                total = 0
                for w in range(1, 53):
                    ra = assignments[a["id"]].get(w, "")
                    rb = assignments[b["id"]].get(w, "")
                    if ra in ("A","B","C","D") and rb in ("A","B","C","D"):
                        total += 1
                        if ra == rb:
                            shared += 1
                print(f"  Cohort {cid}: {a['name']} + {b['name']}: {shared}/{total} floor weeks on same team")

    # Verify Max Consecutive Floors
    print("\n=== CONSECUTIVE FLOOR VERIFICATION ===")
    max_floor_streak = 0
    max_team_streak = 0
    for rid, weeks in assignments.items():
        res = next(r for r in residents_data if r["id"] == rid)
        
        # Check floor streak (A,B,C,D,G,NF,SWING)
        current_streak = 0
        for w in range(1, 53):
            rot = weeks.get(w, "")
            if rot in ["A", "B", "C", "D", "G", "NF", "SWING"]:
                current_streak += 1
            else:
                max_floor_streak = max(max_floor_streak, current_streak)
                current_streak = 0
        max_floor_streak = max(max_floor_streak, current_streak)

        # Check same team streak (A,B,C,D)
        for team in ["A", "B", "C", "D"]:
            team_streak = 0
            for w in range(1, 53):
                rot = weeks.get(w, "")
                if rot == team:
                    team_streak += 1
                else:
                    max_team_streak = max(max_team_streak, team_streak)
                    team_streak = 0
            max_team_streak = max(max_team_streak, team_streak)

    print(f"  Max Consecutive Floor Weeks Found: {max_floor_streak} (Should be <= 4)")
    print(f"  Max Consecutive Same-Team Weeks Found: {max_team_streak} (Should be <= 4)")
    if max_floor_streak <= 4 and max_team_streak <= 4:
         print("  CONSTRAINTS MET ✓")
    else:
         print("  CONSTRAINTS FAILED ❌")

else:
    print(f"Conflicts: {conflicts}")

db.close()
