from database import SessionLocal
from models import Resident, Cohort, Year

db = SessionLocal()
y = db.query(Year).filter(Year.name == '2026-2027').first()
if not y:
    print("Year 2026-2027 not found")
else:
    residents = db.query(Resident).filter(Resident.year_id == y.id).all()
    c_counts = {}
    c_names = {}
    for r in residents:
        if r.pgy in ['PGY1', 'TY']: # Only care about Interns/TYs for bottleneck
            # Actually, TYs are excluded from clinic, so only PGY1s matter for the cohort constraint
            if r.pgy == 'PGY1':
                cid = r.cohort_id
                c_counts[cid] = c_counts.get(cid, 0) + 1
                if cid and cid not in c_names:
                    c = db.query(Cohort).get(cid)
                    c_names[cid] = c.name if c else str(cid)

    print("PGY1 Cohort Sizes:")
    for cid, n in c_counts.items():
        name = c_names.get(cid, "None")
        print(f"Cohort {cid} ({name}): {n}")

db.close()
