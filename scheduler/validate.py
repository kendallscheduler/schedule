"""
Post-schedule validation and dry-run feasibility checks.
"""

from typing import Dict, List, Tuple
from .models import ScheduleContext, NIGHT_CODES, FLOOR_CODES


ED_CODES = {"ED"}
CARDIO_RAM_CODES = {"CARDIO-RAM", "CARDIO-RAM *"}


def validate_assignments(
    assignments: Dict[str, Dict[int, str]],
    ctx: ScheduleContext,
) -> Tuple[bool, List[str]]:
    """
    Validate a schedule against hard constraints.
    Returns (is_valid, list_of_violation_messages).
    """
    violations = []
    residents = {r.name: r for r in ctx.residents}

    for name, weeks in assignments.items():
        res = residents.get(name)
        if not res:
            continue
        codes = [weeks.get(w, "") for w in range(1, ctx.week_count + 1)]

        # Vacation count
        vac_count = sum(1 for c in codes if c == "VACATION")
        if vac_count != ctx.config.vacation_weeks_per_resident:
            violations.append(f"{name}: vacation weeks = {vac_count} (expected {ctx.config.vacation_weeks_per_resident})")

        # Night count
        night_count = sum(1 for c in codes if c in NIGHT_CODES)
        if night_count > ctx.config.max_nights_per_year:
            violations.append(f"{name}: nights = {night_count} (max {ctx.config.max_nights_per_year})")

        # Consecutive nights
        m_consecutive = ctx.config.max_consecutive_nights
        for i in range(len(codes) - m_consecutive):
            window = codes[i:i + m_consecutive + 1]
            if sum(1 for c in window if c in NIGHT_CODES) > m_consecutive:
                violations.append(
                    f"{name}: >{m_consecutive} consecutive nights weeks {i+1}-{i+1+m_consecutive}")

        # PGY1 ED in July
        if res.pgy == 1 and not res.is_ty:
            for w in ctx.config.july_weeks:
                if weeks.get(w) in ED_CODES:
                    violations.append(f"{name}: PGY1 in ED week {w} (July)")

        # PGY1 Ramirez
        if res.pgy == 1 and not res.is_ty:
            for w in range(1, ctx.config.ramirez_forbidden_until_week + 1):
                if weeks.get(w) in CARDIO_RAM_CODES:
                    violations.append(
                        f"{name}: PGY1 CARDIO-RAM week {w} (before mid-Aug)")

    # ED cap per week
    for w in range(1, ctx.week_count + 1):
        ed = sum(1 for a in assignments.values() if a.get(w) in ED_CODES)
        if ed > ctx.config.ed_cap_per_week:
            violations.append(f"Week {w}: ED count = {ed} (max {ctx.config.ed_cap_per_week})")

    # Floor coverage per week (A+B+C+D ≥ 12)
    for w in range(1, ctx.week_count + 1):
        floor = sum(1 for a in assignments.values() if a.get(w) in FLOOR_CODES)
        if floor < 12:
            violations.append(f"Week {w}: floor count = {floor} (min 12)")

    return len(violations) == 0, violations


def dry_run_vacation_feasibility(ctx: ScheduleContext) -> Tuple[bool, List[str]]:
    """Check if hard vacation requests leave enough residents for coverage."""
    msgs = []
    vac_per_week = {}
    for vreq in ctx.vacation_requests:
        if not vreq.hard_lock:
            continue
        for w in range(vreq.start_week, vreq.start_week + vreq.length_weeks):
            if 1 <= w <= ctx.week_count:
                vac_per_week[w] = vac_per_week.get(w, 0) + 1

    n = len(ctx.residents)
    
    # Calculate required working residents from CoverageRules
    sr_required = sum(r.senior_per_unit * r.required_per_week for r in ctx.coverage_rules)
    jr_required = sum(r.intern_per_unit * r.required_per_week for r in ctx.coverage_rules)
    total_required = sr_required + jr_required
    
    # Use config threshold if it's higher than the calculated sum
    min_working = max(total_required, ctx.config.min_working_residents)
    
    for w, cnt in sorted(vac_per_week.items()):
        avail = n - cnt
        if avail < min_working:
            msgs.append(
                f"Week {w}: {cnt} on vacation → {avail} available (need ≥{min_working})")
    
    return len(msgs) == 0, msgs
