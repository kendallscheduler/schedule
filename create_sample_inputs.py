#!/usr/bin/env python3
"""Create sample input Excel files for the AutoScheduler."""

import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent

# VACATION_REQUESTS: ResidentName, PGY, Year, BlockType, StartWeek#, EndWeek#, Priority, HardConstraint
vacation = pd.DataFrame([
    {"ResidentName": "B. Perez", "PGY": 1, "Year": 2026, "BlockType": "VAC1", "StartWeek": 26, "EndWeek": 27, "Priority": 1, "HardConstraint": "N"},
    {"ResidentName": "L. Duarte", "PGY": 1, "Year": 2026, "BlockType": "VAC1", "StartWeek": 30, "EndWeek": 31, "Priority": 2, "HardConstraint": "N"},
])
with pd.ExcelWriter(BASE / "vacation_requests.xlsx", engine="openpyxl") as w:
    vacation.to_excel(w, sheet_name="VACATION_REQUESTS", index=False)

# REQUIREMENTS: PGY, Category, RequiredWeeks
requirements = pd.DataFrame([
    {"PGY": 1, "Category": "ICU", "RequiredWeeks": 8},
    {"PGY": 1, "Category": "FLOORS", "RequiredWeeks": 20},
    {"PGY": 1, "Category": "CLINIC", "RequiredWeeks": 14},
    {"PGY": 1, "Category": "CARDIO", "RequiredWeeks": 2},
    {"PGY": 1, "Category": "ID", "RequiredWeeks": 2},
    {"PGY": 1, "Category": "ED", "RequiredWeeks": 2},
    {"PGY": 1, "Category": "VACATION", "RequiredWeeks": 4},
    {"PGY": 2, "Category": "ICU", "RequiredWeeks": 8},
    {"PGY": 2, "Category": "FLOORS", "RequiredWeeks": 16},
    {"PGY": 2, "Category": "CLINIC", "RequiredWeeks": 14},
    {"PGY": 2, "Category": "CARDIO", "RequiredWeeks": 4},
    {"PGY": 2, "Category": "ID", "RequiredWeeks": 2},
    {"PGY": 2, "Category": "ED", "RequiredWeeks": 2},
    {"PGY": 2, "Category": "NEURO", "RequiredWeeks": 2},
    {"PGY": 2, "Category": "VACATION", "RequiredWeeks": 4},
])
with pd.ExcelWriter(BASE / "requirements.xlsx", engine="openpyxl") as w:
    requirements.to_excel(w, sheet_name="REQUIREMENTS", index=False)

# COMPLETED: ResidentName, Category, CompletedWeeks, Comments (optional - prior year carryover)
completed = pd.DataFrame([
    # Example: {"ResidentName": "M. Garcia", "Category": "ED", "CompletedWeeks": 2, "Comments": "PGY1"},
])
with pd.ExcelWriter(BASE / "completed.xlsx", engine="openpyxl") as w:
    if not completed.empty:
        completed.to_excel(w, sheet_name="COMPLETED", index=False)
    else:
        pd.DataFrame(columns=["ResidentName", "Category", "CompletedWeeks", "Comments"]).to_excel(
            w, sheet_name="COMPLETED", index=False
        )

print("Created: vacation_requests.xlsx, requirements.xlsx, completed.xlsx")
