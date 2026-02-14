#!/usr/bin/env python3
"""Minimal engine test to isolate infeasibility."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import solve

# Coverage needs 21 people/week (9 sr + 12 jr) + clinic cohort (~5) = 26+; with vacation need more
residents = []
rid = 1
for i in range(12):  # seniors
    residents.append({
        "id": rid, "name": f"Sr{i+1}", "pgy": "PGY2", "is_senior": True, "is_intern": False,
        "cohort_id": (i % 5) + 1,
    })
    rid += 1
for i in range(18):  # interns (12 coverage + 6 for clinic overlap)
    residents.append({
        "id": rid, "name": f"Jr{i+1}", "pgy": "PGY1", "is_senior": False, "is_intern": True,
        "cohort_id": (i % 5) + 1,
    })
    rid += 1

# Bare minimum reqs
reqs = {
    "PGY1:": [
        {"category": "FLOORS", "required_weeks": 8}, {"category": "ICU", "required_weeks": 4},
        {"category": "CLINIC", "required_weeks": 4}, {"category": "VACATION", "required_weeks": 4},
        {"category": "NF", "required_weeks": 2}, {"category": "ICU_NIGHT", "required_weeks": 1},
    ],
    "PGY2:": [
        {"category": "FLOORS", "required_weeks": 8}, {"category": "ICU", "required_weeks": 4},
        {"category": "CLINIC", "required_weeks": 4}, {"category": "VACATION", "required_weeks": 4},
        {"category": "NF", "required_weeks": 2}, {"category": "ICU_NIGHT", "required_weeks": 1},
    ],
}

# Try without cohort clinic forcing first
cohort_defs = []  # No forcing - just clinic_count <= 12

assignments, status, conflicts = solve(
    residents=residents,
    requirements_by_pgy=reqs,
    completions_by_resident={},
    vacation_requests=[],
    cohort_defs=cohort_defs,
    time_limit=60,
)

print(f"Status: {status}")
if assignments:
    print(f"OK: {len(assignments)} residents")
else:
    for c in conflicts:
        print(f"  {c}")
