from database import SessionLocal
from models import Resident

db = SessionLocal()
ids = [52, 54, 55, 57, 59, 60, 67, 69, 75, 77, 78]
residents = db.query(Resident).filter(Resident.id.in_(ids)).all()
for r in residents:
    print(f'{r.id}: {r.name} ({r.pgy}) is_senior={r.is_senior}')
db.close()
