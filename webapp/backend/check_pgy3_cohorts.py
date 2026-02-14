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
    c_weeks = {}
    
    # Check only Seniors
    for r in residents:
        if r.pgy in ['PGY2', 'PGY3']:
            cid = r.cohort_id
            if r.pgy == 'PGY3':
                c_counts[cid] = c_counts.get(cid, 0) + 1
            if cid and cid not in c_names:
                c = db.query(Cohort).get(cid)
                c_names[cid] = c.name if c else str(cid)
                c_weeks[cid] = c.clinic_weeks

    print("PGY3 Cohort Sizes and Clinic Weeks:")
    for cid, n in c_counts.items():
        name = c_names.get(cid, "None")
        weeks = c_weeks.get(cid, "[]")
        print(f"Cohort {cid} ({name}): Size {n}, Clinic Weeks: {weeks}")

db.close()
