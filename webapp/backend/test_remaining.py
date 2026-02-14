
from database import SessionLocal
from models import Resident, Requirement, Completion, ScheduleAssignment, Year

db = SessionLocal()
year_id = 1
residents = db.query(Resident).filter(Resident.year_id == year_id).all()

def _reqs_for_resident(res):
    q = db.query(Requirement).filter(Requirement.pgy == res.pgy)
    q = q.filter((Requirement.track.is_(None)) | (Requirement.track == res.track))
    all_reqs = list(q.all())
    by_cat = {}
    for req in sorted(all_reqs, key=lambda r: (1 if r.track else 0)):
        by_cat[req.category] = req
    return list(by_cat.values())

reqs = {r.id: _reqs_for_resident(r) for r in residents}
comps = {}
for c in db.query(Completion).all():
    comps.setdefault(c.resident_id, {})[c.category] = c.completed_weeks

CAT_ROTS = {
    "CLINIC": ["CLINIC", "CLINIC *"],
    "CARDIO": ["CARDIO", "CARDIO-RAM", "CARDIO-HCA"],
    "ED": ["ED"], "ID": ["ID"], "NEURO": ["NEURO"],
    "VACATION": ["VACATION"],
    "GERIATRICS": ["GERIATRICS"],
    "GEN SURG": ["TRAUMA", "SICU", "PLASTIC", "GEN SURG"],
    "ELECTIVE": ["ELECTIVE", "CARDIO", "CARDIO-RAM", "CARDIO-HCA", "ID", "NEURO", "GERIATRICS", "GEN SURG", "ANESTHESIA", "ICU H"],
}
FLOOR_ROTS = ["A", "B", "C", "D", "G"]
ICU_ROTS = ["ICU", "ICU E", "ICU N"]

assignments = {}
for a in db.query(ScheduleAssignment).filter(ScheduleAssignment.year_id == year_id).all():
    assignments.setdefault(a.resident_id, {})[a.week_number] = a.rotation_code

out = []
for r in residents:
    comp = comps.get(r.id, {})
    assigns = assignments.get(r.id, {}) or {}
    resident_reqs = reqs.get(r.id, [])

    def _eff(cat):
        return max(0, comp.get(cat, 0))

    done = {cat: _eff(cat) for cat in CAT_ROTS.keys()}
    for k in ["FLOORS", "ICU", "NF", "ICU_NIGHT", "SWING"]:
        done[k] = _eff(k)

    for w, rot in assigns.items():
        if rot in FLOOR_ROTS: done["FLOORS"] = done.get("FLOORS", 0) + 1
        if rot in ICU_ROTS:   done["ICU"] = done.get("ICU", 0) + 1
        if rot == "ICU N":    done["ICU_NIGHT"] = done.get("ICU_NIGHT", 0) + 1
        if rot == "NF":       done["NF"] = done.get("NF", 0) + 1
        if rot == "SWING":    done["SWING"] = done.get("SWING", 0) + 1
        for cat, rots in CAT_ROTS.items():
            if rot in rots:
                done[cat] = done.get(cat, 0) + 1

    clinic_cnt = sum(1 for rot in assigns.values() if rot in ("CLINIC", "CLINIC *"))
    req_clinic = next((x.required_weeks for x in resident_reqs if x.category == "CLINIC"), 0)
    clinic_overflow = max(0, _eff("CLINIC") + clinic_cnt - req_clinic)
    done["ELECTIVE"] = done.get("ELECTIVE", 0) + clinic_overflow

    core_categories = {"CARDIO", "ID", "ED", "NEURO", "GERIATRICS"}
    seen_cats = set()
    for req in resident_reqs:
        required = req.required_weeks
        completed = max(0, done.get(req.category, 0))
        remaining = max(0, required - completed)
        seen_cats.add(req.category)
        out.append({"r": r.name, "cat": req.category, "done": completed})

print(f"Success. Count: {len(out)}")
db.close()
