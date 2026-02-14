from database import SessionLocal
from models import Resident, Year

db = SessionLocal()
year = db.query(Year).filter(Year.name == "2026-2027").first()
if not year:
    print("Year 2026-2027 not found")
else:
    residents = db.query(Resident).filter(Resident.year_id == year.id).all()
    print(f"Total residents for {year.name}: {len(residents)}")
    
    pgy_counts = {}
    for r in residents:
        pgy_counts[r.pgy] = pgy_counts.get(r.pgy, 0) + 1
    
    for pgy, count in pgy_counts.items():
        print(f"{pgy}: {count}")

db.close()
