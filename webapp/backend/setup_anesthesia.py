
from database import SessionLocal
from models import Rotation, Resident

db = SessionLocal()

# 1. Add ANESTHESIA rotation if missing
anes = db.query(Rotation).filter(Rotation.code == "ANESTHESIA").first()
if not anes:
    db.add(Rotation(code="ANESTHESIA", type="elective", is_night=False, staffing_role_allowed="both", counts_toward_category="ANESTHESIA"))
    print("Added ANESTHESIA rotation code.")

# 2. Assign 'anesthesia' track to last 4 TYs (TY 05 - TY 08)
tys = db.query(Resident).filter(Resident.pgy == "TY", Resident.year_id == 2).order_by(Resident.name).all()
# Sort by name TY 01... TY 08
tys.sort(key=lambda x: x.name)

# Take the last 4 and set track='anesthesia'
for ty in tys[-4:]:
    ty.track = "anesthesia"
    print(f"Set track='anesthesia' for {ty.name}")

db.commit()
db.close()
