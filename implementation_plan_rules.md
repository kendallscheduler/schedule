# Implementation Plan: Data-Driven Scheduling Rules

The current system has many "hidden" rules hardcoded in the Python scripts. To give you more control, we will move these rules into the Excel workbook where you can modify them directly.

## 1. Connect the `COVERAGE_RULES` Sheet
Currently, the solver ignores the `COVERAGE_RULES` sheet. We will update `solver.py` to use the staffing levels you define there.
- **Benefit**: You can change how many residents are needed for Floors, ICU, etc., just by updating a cell in Excel.

## 2. Add a `SOLVER_CONFIG` Sheet
We will introduce a new sheet for global rules that are currently hardcoded.
- **Nights Limit**: Max night shifts per year (currently 8).
- **Vacation Count**: Required weeks (currently 4).
- **ED Capacity**: Max residents in ED per week (currently 3).
- **Restricted Weeks**: Week numbers for Ramirez restriction and July rules.

## 3. Improved Feasibility Feedback
If a schedule cannot be generated, we will update the "CONFLICTS" sheet to be more specific. Instead of just saying it failed, it will tell you which week and which rule (e.g., "Week 12: Cannot meet Floor A senior requirement") is causing the issue.

## 4. Requirement Sensitivity
We will add a "Mandatory" toggle to requirements in `REQUIREMENTS_TARGETS`. 
- If a requirement is mandatory, the solver will fail if it's not met. 
- If not, it will treat it as "Best Effort" (current behavior).

---
**Would you like me to start by connecting the `COVERAGE_RULES` sheet so you can begin testing your own staffing requirements?**
