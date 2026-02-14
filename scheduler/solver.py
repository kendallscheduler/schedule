"""
OR-Tools CP-SAT scheduling engine (v2).
Assigns rotations to resident-weeks enforcing exact coverage composition,
night limits, ED rules, Ramirez restriction, clinic cadence, and vacation.

Grounded in the actual workbook structure.
"""

from ortools.sat.python import cp_model
from typing import Dict, List, Optional, Tuple

from .models import (
    ScheduleContext, Resident, VacationRequest, CoverageRule,
    SOLVER_ROTATION_CODES, NIGHT_CODES, FLOOR_CODES,
)

# Build index
ROT_CODES = list(SOLVER_ROTATION_CODES)
ROT_IDX = {c: i for i, c in enumerate(ROT_CODES)}
N_ROT = len(ROT_CODES)

# Index sets
IDX_A     = ROT_IDX["A"]
IDX_B     = ROT_IDX["B"]
IDX_C     = ROT_IDX["C"]
IDX_D     = ROT_IDX["D"]
IDX_G     = ROT_IDX["G"]
IDX_ICU   = ROT_IDX["ICU"]
IDX_ICUE  = ROT_IDX["ICU E"]
IDX_ICUN  = ROT_IDX["ICU N"]
IDX_NF    = ROT_IDX["NF"]
IDX_SWING = ROT_IDX["SWING"]
IDX_CLINIC = ROT_IDX["CLINIC"]
IDX_CLINIC_STAR = ROT_IDX["CLINIC *"]
IDX_ED    = ROT_IDX["ED"]
IDX_CARDIO = ROT_IDX["CARDIO"]
IDX_CARDIO_RAM = ROT_IDX["CARDIO-RAM"]
IDX_CARDIO_HCA = ROT_IDX["CARDIO-HCA"]
IDX_ID    = ROT_IDX["ID"]
IDX_NEURO = ROT_IDX["NEURO"]
IDX_VAC   = ROT_IDX["VACATION"]

FLOOR_ABCD = [IDX_A, IDX_B, IDX_C, IDX_D]
ICU_DAY    = [IDX_ICU, IDX_ICUE]
NIGHT_IDX  = [IDX_ICUN, IDX_NF]
CLINIC_IDX = [IDX_CLINIC, IDX_CLINIC_STAR]
CARDIO_ALL = [IDX_CARDIO, IDX_CARDIO_RAM, IDX_CARDIO_HCA]


def _indicator(model, var, target_idx, name=""):
    """Return a BoolVar that is 1 iff var == target_idx."""
    b = model.NewBoolVar(name)
    model.Add(var == target_idx).OnlyEnforceIf(b)
    model.Add(var != target_idx).OnlyEnforceIf(b.Not())
    return b


def _indicator_in(model, var, idx_list, name=""):
    """Return a BoolVar that is 1 iff var ∈ idx_list."""
    if len(idx_list) == 1:
        return _indicator(model, var, idx_list[0], name)
    eqs = [_indicator(model, var, i, "") for i in idx_list]
    b = model.NewBoolVar(name)
    model.Add(sum(eqs) >= 1).OnlyEnforceIf(b)
    model.Add(sum(eqs) == 0).OnlyEnforceIf(b.Not())
    return b


def solve(
    ctx: ScheduleContext,
    time_limit_seconds: int = 300,
) -> Tuple[Optional[Dict[str, Dict[int, str]]], str, List[str]]:
    """
    Returns (assignments, status_str, conflict_messages).
    assignments = {resident_name: {week: rotation_code}} or None if infeasible.
    """
    model = cp_model.CpModel()
    residents = ctx.residents
    names = [r.name for r in residents]
    N = len(residents)
    weeks = list(range(1, ctx.week_count + 1))

    # Classify residents
    senior_idxs = [i for i, r in enumerate(residents) if r.is_senior]
    intern_idxs = [i for i, r in enumerate(residents) if r.is_intern]

    # ── Decision variables ──
    assign = {}
    for r in range(N):
        for w in weeks:
            assign[(r, w)] = model.NewIntVar(0, N_ROT - 1, f"a_{r}_{w}")

    # ── Precompute indicators we'll reuse ──
    # on_X[r][w] = BoolVar  (lazily populated)
    is_on = {}  # (r, w, idx) -> BoolVar

    def get_ind(r, w, idx):
        key = (r, w, idx)
        if key not in is_on:
            is_on[key] = _indicator(model, assign[(r, w)], idx, f"i_{r}_{w}_{idx}")
        return is_on[key]

    def get_ind_set(r, w, idx_list, tag=""):
        key = (r, w, tuple(idx_list))
        if key not in is_on:
            is_on[key] = _indicator_in(model, assign[(r, w)], idx_list, f"is_{tag}_{r}_{w}")
        return is_on[key]

    # ══════════════════════════════════════════════════════════
    # 1. VACATION: exactly N weeks per resident
    # ══════════════════════════════════════════════════════════
    for r in range(N):
        vac_bools = [get_ind(r, w, IDX_VAC) for w in weeks]
        model.Add(sum(vac_bools) == ctx.config.vacation_weeks_per_resident)

    # 2. Hard vacation locks
    for vreq in ctx.vacation_requests:
        if not vreq.hard_lock:
            continue
        ri = None
        for i, res in enumerate(residents):
            if res.name == vreq.resident_name:
                ri = i
                break
        if ri is None:
            continue
        for w in range(vreq.start_week, vreq.start_week + vreq.length_weeks):
            if 1 <= w <= ctx.week_count:
                model.Add(assign[(ri, w)] == IDX_VAC)

    # ══════════════════════════════════════════════════════════
    # 3. COVERAGE — drove by COVERAGE_RULES sheet
    # ══════════════════════════════════════════════════════════
    POOL_MAP = {
        "FLOOR_A": [IDX_A],
        "FLOOR_B": [IDX_B],
        "FLOOR_C": [IDX_C],
        "FLOOR_D": [IDX_D],
        "ICU_DAY": ICU_DAY,
        "NF":      [IDX_NF],
        "ICU_NIGHT": [IDX_ICUN],
        "SWING":   [IDX_SWING],
        "TEAM_G":  [IDX_G],
    }

    for rule in ctx.coverage_rules:
        idx_list = POOL_MAP.get(rule.rotation_pool)
        if not idx_list or rule.required_per_week <= 0:
            if rule.rotation_pool == "TEAM_G":
                # Special: restrict interns from G even if 0 required
                for r in intern_idxs:
                    for w in weeks:
                        model.Add(assign[(r, w)] != IDX_G)
            continue
        
        for w in weeks:
            sr_pool = [get_ind_set(r, w, idx_list, rule.rotation_pool.lower()) for r in senior_idxs]
            jr_pool = [get_ind_set(r, w, idx_list, rule.rotation_pool.lower()) for r in intern_idxs]
            
            if rule.senior_per_unit > 0:
                model.Add(sum(sr_pool) >= rule.senior_per_unit * rule.required_per_week)
            if rule.intern_per_unit > 0:
                model.Add(sum(jr_pool) >= rule.intern_per_unit * rule.required_per_week)
            
            if rule.rotation_pool == "TEAM_G":
                # Stay seniors-only
                for r in intern_idxs:
                    model.Add(assign[(r, w)] != IDX_G)

    # ══════════════════════════════════════════════════════════
    # 4. ED: max N per week, no PGY1 in July
    # ══════════════════════════════════════════════════════════
    for w in weeks:
        ed_all = [get_ind(r, w, IDX_ED) for r in range(N)]
        model.Add(sum(ed_all) <= ctx.config.ed_cap_per_week)
    for r in range(N):
        res = residents[r]
        if res.pgy == 1 and not res.is_ty:
            for w in ctx.config.july_weeks:
                if w <= ctx.week_count:
                    model.Add(assign[(r, w)] != IDX_ED)

    # ══════════════════════════════════════════════════════════
    # 5. Ramirez: no PGY1 on CARDIO-RAM before configured week
    # ══════════════════════════════════════════════════════════
    for r in range(N):
        res = residents[r]
        if res.pgy == 1 and not res.is_ty:
            for w in range(1, ctx.config.ramirez_forbidden_until_week + 1):
                if w <= ctx.week_count:
                    model.Add(assign[(r, w)] != IDX_CARDIO_RAM)

    # ══════════════════════════════════════════════════════════
    # 6. Night limits: max N/year, max M consecutive
    # ══════════════════════════════════════════════════════════
    for r in range(N):
        night_bools = [get_ind_set(r, w, NIGHT_IDX, "night") for w in weeks]
        model.Add(sum(night_bools) <= ctx.config.max_nights_per_year)
        # No more than M consecutive
        m_consecutive = ctx.config.max_consecutive_nights
        for s in range(len(weeks) - m_consecutive):
            model.Add(sum(night_bools[s:s + m_consecutive + 1]) <= m_consecutive)

    # ══════════════════════════════════════════════════════════
    # 7. REQUIREMENT TARGETS — Soft Constraints (maximize compliance)
    # ══════════════════════════════════════════════════════════
    # Map requirement category to solver rotation indices
    REQ_CAT_TO_IDX = {
        "ICU":     ICU_DAY + [IDX_ICUN],  # day + night combined
        "FLOORS":  FLOOR_ABCD + [IDX_G, IDX_NF, IDX_SWING], # Per note: A/B/C/D/G + NF +/- Swing
        "CLINIC":  CLINIC_IDX,
        "CARDIO":  CARDIO_ALL,
        "ID":      [IDX_ID],
        "ED":      [IDX_ED],
        "NEURO":   [IDX_NEURO],
        "NF":      [IDX_NF],
        "SWING":   [IDX_SWING],
    }
    
    total_deficit = []
    for r_idx in range(N):
        res = residents[r_idx]
        pgy_label = "TY" if res.is_ty else f"PGY{res.pgy}"
        matching_reqs = [rq for rq in ctx.requirements if rq.pgy == pgy_label]
        for rq in matching_reqs:
            idx_list = REQ_CAT_TO_IDX.get(rq.category)
            if idx_list is None or rq.category == "VACATION":
                continue 
            
            # Sum of weeks on this category
            cat_bools = [get_ind_set(r_idx, w, idx_list, rq.category.lower()) for w in weeks]
            
            # Mandatory vs Soft Deficit
            if rq.is_mandatory:
                model.Add(sum(cat_bools) >= rq.required_weeks)
            else:
                deficit = model.NewIntVar(0, rq.required_weeks, f"def_{r_idx}_{rq.category}")
                model.Add(sum(cat_bools) + deficit >= rq.required_weeks)
                # Weight deficit heavily (100) vs transitions (1)
                total_deficit.append(deficit * 100)

    # ══════════════════════════════════════════════════════════
    # 8. Clinic cadence — hard constraint for cohort clinic weeks
    # ══════════════════════════════════════════════════════════
    for coh_def in ctx.cohort_defs:
        coh_residents = [i for i, r in enumerate(residents)
                         if r.cohort_id == coh_def.cohort_id]
        for w in coh_def.clinic_weeks:
            if 1 <= w <= ctx.week_count:
                for r in coh_residents:
                    # Force: on this cohort's clinic week, the resident is on CLINIC
                    clinic_b = get_ind_set(r, w, CLINIC_IDX, "cl")
                    model.Add(clinic_b == 1)

    # ══════════════════════════════════════════════════════════
    # Objective: minimize rotation changes (prefer 2-4 week blocks)
    # + soft vacation priority honoring
    # ══════════════════════════════════════════════════════════
    change_cost = []
    for r in range(N):
        for w in range(1, ctx.week_count):
            diff = model.NewBoolVar(f"ch_{r}_{w}")
            model.Add(assign[(r, w)] != assign[(r, w + 1)]).OnlyEnforceIf(diff)
            model.Add(assign[(r, w)] == assign[(r, w + 1)]).OnlyEnforceIf(diff.Not())
            change_cost.append(diff)

    # Soft vacation: reward placing vacation on requested weeks
    vac_bonus = []
    for vreq in ctx.vacation_requests:
        if vreq.hard_lock:
            continue
        ri = None
        for i, res in enumerate(residents):
            if res.name == vreq.resident_name:
                ri = i
                break
        if ri is None:
            continue
        weight = 6 - vreq.priority  # priority 1 → weight 5
        for w in range(vreq.start_week, vreq.start_week + vreq.length_weeks):
            if 1 <= w <= ctx.week_count:
                vb = get_ind(ri, w, IDX_VAC)
                vac_bonus.append(vb * weight)

    model.Minimize(
        sum(change_cost)
        + sum(total_deficit)
        - 3 * sum(vac_bonus)
    )

    # ── Solve ──
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_workers = 8
    if ctx.random_seed is not None:
        solver.parameters.random_seed = ctx.random_seed

    status = solver.Solve(model)
    conflicts = []

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        assignments = {}
        for r in range(N):
            assignments[names[r]] = {}
            for w in weeks:
                idx = int(solver.Value(assign[(r, w)]))
                assignments[names[r]][w] = ROT_CODES[idx]
        status_str = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
        return assignments, status_str, conflicts

    # Infeasible — try to identify conflicting vacation locks
    conflicts.append(f"Solver status: {solver.StatusName(status)}")
    for vreq in ctx.vacation_requests:
        if vreq.hard_lock:
            conflicts.append(
                f"Hard lock: {vreq.resident_name} weeks "
                f"{vreq.start_week}-{vreq.start_week + vreq.length_weeks - 1} "
                f"(priority {vreq.priority})"
            )
    return None, solver.StatusName(status), conflicts
