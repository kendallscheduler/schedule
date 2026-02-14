from database import SessionLocal
from models import ScheduleAssignment
from sqlalchemy import func

db = SessionLocal()
duplicates = db.query(
    ScheduleAssignment.resident_id,
    ScheduleAssignment.week_number,
    func.count(ScheduleAssignment.id).label('cnt')
).group_by(
    ScheduleAssignment.resident_id,
    ScheduleAssignment.week_number
).having(func.count(ScheduleAssignment.id) > 1).all()

print(f"Found {len(duplicates)} duplicate resident/week assignments.")
for d in duplicates[:10]:
    print(f"Resident {d.resident_id}, Week {d.week_number}: {d.cnt} assignments")
db.close()
