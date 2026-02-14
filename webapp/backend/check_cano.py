from database import SessionLocal
from models import Resident, Year

db = SessionLocal()
res = db.query(Resident).filter(Resident.name == "D. Cano").all()
for r in res:
    year = db.query(Year).filter(Year.id == r.year_id).first()
    print(f'Resident: {r.name}, ID: {r.id}, Year ID: {r.year_id}, Year Name: {year.name if year else "Unknown"}')
db.close()
