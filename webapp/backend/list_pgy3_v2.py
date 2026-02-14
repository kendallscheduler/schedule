from database import SessionLocal
from models import Resident, Year

db = SessionLocal()
year = db.query(Year).filter(Year.name == "2025-2026").first()
res = db.query(Resident).filter(Resident.year_id == year.id, Resident.pgy == 'PGY3').all()
for r in res:
    print(f'{r.id}: {r.name}')
db.close()
