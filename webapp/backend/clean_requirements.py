
from database import SessionLocal
from models import Requirement

db = SessionLocal()
db.query(Requirement).delete()
db.commit()
print("Requirements table cleared.")
db.close()
