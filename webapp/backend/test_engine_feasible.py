#!/usr/bin/env python3
"""Test engine with a minimal feasible roster: 9 seniors, 29 interns (38 total for clinic)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import solve

# Minimal feasible roster: 9 seniors, 29 interns = 38 total
# Coverage needs: 9 sr, 12 jr. Clinic needs: 38 * 14 >= 520.
residents = []
rid = 1
for i in range(9):
    residents.append({
        "id": rid, "name": f"Senior {i+1}", "pgy": "PGY2", "is_senior": True, "is_intern": False,
        "cohort_id": (i % 5) + 1,
    })
    rid += 1
for i in range(29):
    residents.append({
        "id": rid, "name": f"Intern {i+1}", "pgy": "PGY1", "is_senior": False, "is_intern": True,
        "cohort_id": (i % 5) + 1,
    })
    rid += 1

# Relaxed requirements that fit in 52 weeks (seed totals can exceed 52; these are per-year for test)
reqs = {
    "PGY1:": [
        {"category": "FLOORS", "required_weeks": 12}, {"category": "ICU", "required_weeks": 4},
        {"category": "CLINIC", "required_weeks": 10}, {"category": "VACATION", "required_weeks": 4},
        {"category": "NF", "required_weeks": 2}, {"category": "ICU_NIGHT", "required_weeks": 1},
        {"category": "CARDIO", "required_weeks": 2}, {"category": "ID", "required_weeks": 1},
        {"category": "NEURO", "required_weeks": 1}, {"category": "ED", "required_weeks": 2},
        {"category": "GERIATRICS", "required_weeks": 1},
    ],
    "PGY2:": [
        {"category": "FLOORS", "required_weeks": 10}, {"category": "ICU", "required_weeks": 4},
        {"category": "CLINIC", "required_weeks": 10}, {"category": "VACATION", "required_weeks": 4},
        {"category": "NF", "required_weeks": 2}, {"category": "ICU_NIGHT", "required_weeks": 1},
        {"category": "CARDIO", "required_weeks": 2}, {"category": "ID", "required_weeks": 1},
        {"category": "NEURO", "required_weeks": 1}, {"category": "ED", "required_weeks": 2},
        {"category": "GERIATRICS", "required_weeks": 1},
    ],
}

clinic_weeks = {
    1: [1, 6, 11, 16, 21, 28, 33, 38, 43, 48],
    2: [2, 7, 12, 17, 22, 29, 34, 39, 44, 49],
    3: [3, 8, 13, 18, 23, 30, 35, 40, 45, 50],
    4: [4, 9, 14, 19, 24, 31, 36, 41, 46],
    5: [5, 10, 15, 20, 25, 32, 37, 47, 52],
}
cohort_defs = [{"cohort_id": cid, "clinic_weeks": weeks} for cid, weeks in clinic_weeks.items()]

assignments, status, conflicts = solve(
    residents=residents,
    requirements_by_pgy=reqs,
    completions_by_resident={},
    vacation_requests=[],
    cohort_defs=cohort_defs,
    time_limit=30,
)

if assignments:
    print(f"OK: {status}, {len(assignments)} residents scheduled")
else:
    print(f"FAIL: {status}")
    for c in conflicts:
        print(f"  - {c}")
    sys.exit(1)
