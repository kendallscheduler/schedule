from database import SessionLocal
from models import Requirement

db = SessionLocal()
reqs = db.query(Requirement).all()
for r in reqs:
    print(f'{r.pgy} {r.category}: {r.required_weeks}')
db.close()
