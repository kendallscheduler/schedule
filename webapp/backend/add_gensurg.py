
from database import SessionLocal
from models import Rotation

db = SessionLocal()

# 1. Add GEN SURG rotation if missing
gs = db.query(Rotation).filter(Rotation.code == "GEN SURG").first()
if not gs:
    db.add(Rotation(code="GEN SURG", type="elective", is_night=False, staffing_role_allowed="both", counts_toward_category="GEN SURG"))
    print("Added GEN SURG rotation code.")

db.commit()
db.close()
