from database import SessionLocal
from models import Resident, Cohort

db = SessionLocal()
cohorts = db.query(Cohort).all()
for c in cohorts:
    count = db.query(Resident).filter(Resident.cohort_id == c.id, Resident.pgy != 'TY').count()
    print(f'{c.name}: {count}')
db.close()
