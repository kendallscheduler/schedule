# Master Schedule AutoScheduler v2

Constraint-based residency master schedule generator. Uses the existing Excel workbook as the **single source of truth** — all data-entry, scheduling, and validation happen inside the same `.xlsx` file.

## Quick Start

```bash
# Install dependencies
pip install openpyxl ortools pandas

# Step 1: Add data-entry sheets to the workbook
python run_scheduler.py setup --workbook "2025 Updated Schedule - Copy 2026.xlsx"

# Step 2: (Optional) Fill in VACATION_REQUESTS sheet in Excel, then dry-run
python run_scheduler.py dry-run --workbook "2025 Updated Schedule - Copy 2026.xlsx"

# Step 3: Generate a scheduled workbook
python run_scheduler.py solve \
  --workbook "2026 Unscheduled Master Schedule.xlsx" \
  --out "2026 Master Schedule - Auto.xlsx" \
  --time-limit 300

# Step 4: Promote to next year (PGY-1→PGY-2→PGY-3, clear grid)
python run_scheduler.py next-year \
  --workbook "2025 Updated Schedule - Copy 2026.xlsx" \
  --out "2027 Unscheduled Master Schedule.xlsx"
```

## Workbook Sheets

After running `setup`, the workbook contains these sheets:

| Sheet | Purpose | Editable? |
|-------|---------|-----------|
| **SCHEDULE** | Master grid (rows 4-56, cols D-BC) + formulas (BD-CD) | Assignments only |
| **CATEGORY** | Dropdown list values | Do not change |
| **RESIDENTS** | Auto-extracted resident list with PGY, cohort, row index | Read-only |
| **REQUIREMENTS_TARGETS** | Required weeks per PGY/category | Yes — edit targets here |
| **VACATION_REQUESTS** | Vacation entry: name, week, priority, hard lock | Yes — enter requests here |
| **COVERAGE_RULES** | Weekly staffing minimums per rotation pool | Yes — adjust rules |
| **COHORTS** | Clinic 4+1 cadence week patterns per cohort | Yes — adjust cadence |
| **PROGRESS** | Live remaining-weeks dashboard (formula links to BD-CD) | Read-only |

## VACATION_REQUESTS Format

| Column | Description |
|--------|-------------|
| ResidentName | Must match SCHEDULE col C exactly |
| PGY | PGY1, PGY2, PGY3, or TY |
| RequestType | VAC_BLOCK_1 or VAC_BLOCK_2 |
| StartWeekNumber | 1-52 |
| LengthWeeks | Default 2 |
| Priority | 1-5 (1 = highest) |
| HardLock | Y = must honor, N = soft preference |
| Comments | Free text |

## Hard Constraints (Solver)

| Constraint | Rule |
|------------|------|
| **Floor teams A-D** | Each: 1 senior + 2 interns per week (4 teams always) |
| **ICU day** | 2 seniors + 2 interns per week |
| **Night Float** | 1 senior + 1 intern per week |
| **ICU Night** | 1 senior + 1 intern per week |
| **Swing** | 1 senior per week |
| **Team G** | Seniors only (optional) |
| **Vacation** | Exactly 4 weeks per resident |
| **Nights max** | 8 weeks/year, max 4 consecutive |
| **ED cap** | Max 3 residents/week, no PGY1 in July |
| **Ramirez** | No PGY1 on CARDIO-RAM before week 7 (mid-August) |
| **Requirements** | Each resident meets PGY-level requirement minimums |
| **Clinic cadence** | Cohort members on clinic during their cohort's clinic weeks |

## Soft Objectives

- Minimize rotation changes (prefer 2-4 week blocks)
- Honor soft vacation requests weighted by priority

## File Structure

```
scheduler/
  __init__.py
  models.py           # Data classes, rotation codes, counter mappings
  workbook_sheets.py  # Add/refresh data-entry sheets (Parts A + B)
  parse_inputs.py     # Read from workbook sheets into ScheduleContext
  solver.py           # OR-Tools CP-SAT model
  write_schedule.py   # Write assignments to Excel, add CONFLICTS sheet
  validate.py         # Post-checks and dry-run feasibility
  year_promotion.py   # PGY promotion and next-year creation

run_scheduler.py      # CLI entry point (setup / dry-run / solve / next-year)
create_unscheduled_template.py  # Standalone: clear grid from existing schedule
```

## Dependencies

```
openpyxl>=3.0.0
ortools>=9.0
pandas>=1.3.0
```
