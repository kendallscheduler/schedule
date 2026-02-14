
from database import SessionLocal
from routers.schedule import get_remaining_requirements
import json

db = SessionLocal()
try:
    res = get_remaining_requirements(1, db)
    print(json.dumps(res[:2], indent=2))
except Exception as e:
    import traceback
    print(traceback.format_exc())
finally:
    db.close()
