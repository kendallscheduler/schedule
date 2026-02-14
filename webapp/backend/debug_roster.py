from database import SessionLocal
from models import Resident, Year

db = SessionLocal()
year = db.query(Year).filter(Year.name == "2025-2026").first()
if not year:
    print("Year not found")
else:
    residents = db.query(Resident).filter(Resident.year_id == year.id).all()
    print(f"Total residents for {year.name}: {len(residents)}")
    
    pgy_counts = {}
    for r in residents:
        pgy_counts[r.pgy] = pgy_counts.get(r.pgy, 0) + 1
    
    for pgy, count in pgy_counts.items():
        print(f"{pgy}: {count}")
    
    # Check for duplicates by name
    name_counts = {}
    for r in residents:
        name_counts[r.name] = name_counts.get(r.name, 0) + 1
    
    dupes = [name for name, count in name_counts.items() if count > 1]
    print(f"Residents with duplicate names: {len(dupes)}")
    for name in dupes[:10]:
        r_list = [r for r in residents if r.name == name]
        print(f"  {name}: {[r.id for r in r_list]}")

db.close()
