from database import SessionLocal
from models import Resident

db = SessionLocal()
res = db.query(Resident).filter(Resident.pgy == 'PGY3').all()
for r in res:
    print(f'{r.name}')
db.close()
