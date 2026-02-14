#!/usr/bin/env python3
"""Test engine with user's roster: 28 seniors (14 PGY2, 14 PGY3), 22 interns (14 PGY1, 8 TY)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import solve

residents = []
rid = 1
# 14 PGY2, 14 PGY3 (28 seniors) - assigned to cohorts 1-5
for i in range(14):
    residents.append({
        "id": rid, "name": f"PGY2_{i+1}", "pgy": "PGY2", "is_senior": True, "is_intern": False,
        "cohort_id": (i % 5) + 1, "is_ty": False,
    })
    rid += 1
for i in range(14):
    residents.append({
        "id": rid, "name": f"PGY3_{i+1}", "pgy": "PGY3", "is_senior": True, "is_intern": False,
        "cohort_id": (i % 5) + 1, "is_ty": False,
    })
    rid += 1
# 14 PGY1 (interns with cohort)
for i in range(14):
    residents.append({
        "id": rid, "name": f"PGY1_{i+1}", "pgy": "PGY1", "is_senior": False, "is_intern": True,
        "cohort_id": (i % 5) + 1, "is_ty": False,
    })
    rid += 1
# 8 TY (interns, no cohort)
for i in range(8):
    residents.append({
        "id": rid, "name": f"TY_{i+1}", "pgy": "TY", "is_senior": False, "is_intern": True,
        "cohort_id": None, "is_ty": True,
    })
    rid += 1

# Minimal reqs to test feasibility (annual only, no electives)
reqs = {
    "PGY1:": [
        {"category": "FLOORS", "required_weeks": 20}, {"category": "ICU", "required_weeks": 8},
        {"category": "CLINIC", "required_weeks": 14}, {"category": "VACATION", "required_weeks": 4},
        {"category": "NF", "required_weeks": 2}, {"category": "ICU_NIGHT", "required_weeks": 2},
    ],
    "PGY2:": [
        {"category": "FLOORS", "required_weeks": 16}, {"category": "ICU", "required_weeks": 8},
        {"category": "CLINIC", "required_weeks": 14}, {"category": "VACATION", "required_weeks": 4},
        {"category": "NF", "required_weeks": 2}, {"category": "ICU_NIGHT", "required_weeks": 2},
    ],
    "PGY3:": [
        {"category": "FLOORS", "required_weeks": 8}, {"category": "ICU", "required_weeks": 4},
        {"category": "CLINIC", "required_weeks": 14}, {"category": "VACATION", "required_weeks": 4},
        {"category": "NF", "required_weeks": 2}, {"category": "ICU_NIGHT", "required_weeks": 2},
    ],
    "TY:": [
        {"category": "FLOORS", "required_weeks": 16}, {"category": "NF", "required_weeks": 4},
        {"category": "ICU", "required_weeks": 4}, {"category": "ICU_NIGHT", "required_weeks": 2},
        {"category": "VACATION", "required_weeks": 4},
    ],
}

cohort_defs = [
    {"cohort_id": 1, "clinic_weeks": [1, 6, 11, 16, 21, 28, 33, 38, 43, 48]},
    {"cohort_id": 2, "clinic_weeks": [2, 7, 12, 17, 22, 29, 34, 39, 44, 49]},
    {"cohort_id": 3, "clinic_weeks": [3, 8, 13, 18, 23, 30, 35, 40, 45, 50]},
    {"cohort_id": 4, "clinic_weeks": [4, 9, 14, 19, 24, 31, 36, 41, 46]},
    {"cohort_id": 5, "clinic_weeks": [5, 10, 15, 20, 25, 32, 37, 47, 52]},
]
assignments, status, conflicts = solve(
    residents=residents,
    requirements_by_pgy=reqs,
    completions_by_resident={},
    vacation_requests=[],
    cohort_defs=cohort_defs,
    time_limit=120,
)

print(f"Status: {status}")
if assignments:
    print(f"OK: {len(assignments)} residents scheduled")
else:
    for c in conflicts:
        print(f"  {c}")
    sys.exit(1)
