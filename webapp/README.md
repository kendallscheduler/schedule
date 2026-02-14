# IM Residency Schedule Generator — Web App

Web-based scheduling software that generates an IM residency master schedule from resident-specific requirements and completed progress.

## Quick Start

### Backend

```bash
cd webapp/backend
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload
```

Backend runs at http://localhost:8000. API docs at http://localhost:8000/docs.

**After code updates to requirements/rotations:** Run `python seed.py` again, or use the **Requirements** page → **Sync to standard spec** button.

### Frontend

```bash
cd webapp/frontend
npm install
npm run dev
```

Frontend runs at http://localhost:3000.

## Import Roster from Excel

1. Create an Excel file with columns: **Name**, **PGY**, **Cohort** (optional).
2. Go to Residents page → Import from Excel.

## Import Residents from Existing Excel

```bash
cd backend
python import_roster_from_excel.py "../../2025 Updated Schedule - Copy 2026.xlsx"
```

## Next Year Rollover

Create next year roster from current year or from uploaded Excel:

- **From DB**: Uses residents in the selected source year
- **From Excel**: Upload current master schedule; parses SCHEDULE sheet (rows 4-56, A=Cohort, B=PGY, C=Name)

Rollover rules:
- PGY1 → PGY2, PGY2 → PGY3, PGY3 → graduate (exclude unless "Include PGY3" checked)
- TY → graduate
- Placeholders: "Intern 01", "Intern 02", ... and "TY 01", "TY 02", ...
- Cohorts: Configurable target interns per cohort (e.g., Cohort 1: 4, Cohort 2: 2, ...)

## Generate Schedule

1. Ensure residents are loaded (import or add manually).
2. (Optional) Add vacation requests.
3. Go to Generate page → **Generate Schedule** (allow 2–5 minutes).
4. **Export to Excel** to download the master schedule.

## Data Model

- **residents** — name, PGY, cohort, constraints
- **requirements** — per-PGY category targets (FLOORS, ICU, CLINIC, etc.)
- **completions** — prior completed weeks per resident
- **vacation_requests** — requested blocks with priority and hard lock
- **schedule_assignments** — resident × week → rotation code

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite, OR-Tools CP-SAT
- Frontend: Next.js, React, TypeScript
