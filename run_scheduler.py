#!/usr/bin/env python3
"""
AutoScheduler CLI (v2) — single-workbook workflow.

The workbook is the source of truth for everything:
  SCHEDULE (residents + assignments + formulas)
  RESIDENTS, REQUIREMENTS_TARGETS, VACATION_REQUESTS,
  COVERAGE_RULES, COHORTS, PROGRESS  (data-entry sheets)

Usage:
  # Step 1: Add/refresh data-entry sheets to the workbook
  python run_scheduler.py setup --workbook "2025 Updated Schedule - Copy 2026.xlsx"

  # Step 2 (optional): Dry-run — check vacation feasibility
  python run_scheduler.py dry-run --workbook "2025 Updated Schedule - Copy 2026.xlsx"

  # Step 3: Generate a scheduled workbook
  python run_scheduler.py solve --workbook "2025 Updated Schedule - Copy 2026.xlsx" \
      --out "2026 Master Schedule - Auto.xlsx" --time-limit 300

  # Step 4: Promote to next year
  python run_scheduler.py next-year --workbook "2025 Updated Schedule - Copy 2026.xlsx" \
      --out "2027 Unscheduled Master Schedule.xlsx"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scheduler.workbook_sheets import setup_all_sheets
from scheduler.parse_inputs import parse_workbook
from scheduler.solver import solve
from scheduler.write_schedule import write_schedule, add_conflicts_sheet
from scheduler.validate import validate_assignments, dry_run_vacation_feasibility
from scheduler.year_promotion import build_next_year


def _resolve(p: str) -> Path:
    pp = Path(p)
    if pp.is_absolute():
        return pp
    return Path(__file__).resolve().parent / pp


def cmd_setup(args):
    """Add/refresh all supporting sheets in the workbook."""
    wb_path = str(_resolve(args.workbook))
    print(f"Setting up sheets in: {wb_path}")
    setup_all_sheets(wb_path)
    print("Done — sheets added/refreshed:")
    print("  RESIDENTS, REQUIREMENTS_TARGETS, VACATION_REQUESTS,")
    print("  COVERAGE_RULES, COHORTS, PROGRESS")


def cmd_dry_run(args):
    """Validate vacation feasibility without solving."""
    wb_path = str(_resolve(args.workbook))
    print(f"Parsing: {wb_path}")
    ctx = parse_workbook(wb_path, random_seed=args.seed)
    print(f"  Residents: {len(ctx.residents)}")
    print(f"  Vacation requests: {len(ctx.vacation_requests)}")
    print(f"  Cohort defs: {len(ctx.cohort_defs)}")

    ok, msgs = dry_run_vacation_feasibility(ctx)
    if ok:
        print("\nVacation feasibility: OK")
    else:
        print("\nVacation feasibility issues:")
        for m in msgs:
            print(f"  {m}")


def cmd_solve(args):
    """Run the constraint solver and produce a scheduled workbook."""
    wb_path = str(_resolve(args.workbook))
    out_path = str(_resolve(args.out))
    print(f"Parsing: {wb_path}")
    ctx = parse_workbook(wb_path, random_seed=args.seed)
    print(f"  Residents: {len(ctx.residents)}")
    print(f"  Vacation requests: {len(ctx.vacation_requests)}")
    print(f"  Coverage rules: {len(ctx.coverage_rules)}")
    print(f"  Cohort defs: {len(ctx.cohort_defs)}")

    # Step 1: dry-run check
    ok, msgs = dry_run_vacation_feasibility(ctx)
    if not ok:
        print("\nWarning — vacation feasibility issues (will attempt anyway):")
        for m in msgs:
            print(f"  {m}")

    # Step 2: solve
    print(f"\nSolving (time limit {args.time_limit}s)...")
    assignments, status, conflicts = solve(ctx, time_limit_seconds=args.time_limit)

    if assignments is None:
        print(f"\nSolver INFEASIBLE: {status}")
        if conflicts:
            print("Conflicts:")
            for c in conflicts:
                print(f"  {c}")
        # Write conflicts to output workbook
        import shutil
        shutil.copy2(wb_path, out_path)
        add_conflicts_sheet(out_path, conflicts)
        print(f"\nConflicts written to: {out_path}")
        sys.exit(1)

    print(f"  Solver status: {status}")

    # Step 3: validate
    valid, violations = validate_assignments(assignments, ctx)
    if valid:
        print("  Validation: OK")
    else:
        print(f"  Validation: {len(violations)} issue(s)")
        for v in violations[:15]:
            print(f"    {v}")
        if len(violations) > 15:
            print(f"    ... and {len(violations) - 15} more")

    # Step 4: write
    print(f"\nWriting schedule to: {out_path}")
    write_schedule(
        template_path=wb_path,
        output_path=out_path,
        assignments=assignments,
        resident_row_map=ctx.resident_row_map,
    )

    if conflicts:
        add_conflicts_sheet(out_path, conflicts)

    # Step 5: refresh PROGRESS sheet in the output
    setup_all_sheets(out_path)
    print("Done.")


def cmd_next_year(args):
    """Create a next-year workbook with promoted PGY levels and cleared grid."""
    wb_path = str(_resolve(args.workbook))
    out_path = str(_resolve(args.out))
    print(f"Building next year from: {wb_path}")
    build_next_year(wb_path, out_path)
    print(f"Created: {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="AutoScheduler — Residency Master Schedule",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", help="Command")

    # setup
    p_setup = sub.add_parser("setup", help="Add/refresh data-entry sheets")
    p_setup.add_argument("--workbook", required=True, help="Workbook path")

    # dry-run
    p_dry = sub.add_parser("dry-run", help="Validate vacation feasibility")
    p_dry.add_argument("--workbook", required=True, help="Workbook path")
    p_dry.add_argument("--seed", type=int, default=None)

    # solve
    p_solve = sub.add_parser("solve", help="Run solver and produce schedule")
    p_solve.add_argument("--workbook", required=True, help="Workbook path")
    p_solve.add_argument("--out", default="2026 Master Schedule - Auto.xlsx")
    p_solve.add_argument("--time-limit", type=int, default=300)
    p_solve.add_argument("--seed", type=int, default=None)

    # next-year
    p_next = sub.add_parser("next-year", help="Promote PGY and create fresh workbook")
    p_next.add_argument("--workbook", required=True, help="Current year workbook")
    p_next.add_argument("--out", required=True, help="Output path for next year")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    dispatch = {
        "setup": cmd_setup,
        "dry-run": cmd_dry_run,
        "solve": cmd_solve,
        "next-year": cmd_next_year,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
