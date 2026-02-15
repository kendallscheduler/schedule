"""OR-Tools CP-SAT scheduling engine for resident-dependent schedules."""
from typing import Dict, List, Optional, Tuple
from ortools.sat.python import cp_model

# Rotation indices — SIMPLIFIED to only allowed rotations
ROT_CODES = [
    "A", "B", "C", "D", "G",
    "ICU", "ICU N", "NF", "SWING",
    "CLINIC", "CLINIC *",
    "ED", "CARDIO",
    "ID", "NEURO", "VACATION",
    "GERIATRICS", "ELECTIVE", "GEN SURG", "TY CLINIC", "ICU H",
]
ROT_IDX = {c: i for i, c in enumerate(ROT_CODES)}
N_ROT = len(ROT_CODES)

FLOOR_ABCD = [ROT_IDX["A"], ROT_IDX["B"], ROT_IDX["C"], ROT_IDX["D"]]
ICU_DAY = [ROT_IDX["ICU"]]  # Single ICU code for day
# Night shifts: NF, ICU N, SWING (all count toward night caps)
NIGHT_IDX = [ROT_IDX["ICU N"], ROT_IDX["NF"], ROT_IDX["SWING"]]
IDX_VAC = ROT_IDX["VACATION"]
IDX_ED = ROT_IDX["ED"]
IDX_SWING = ROT_IDX["SWING"]
IDX_NF = ROT_IDX["NF"]
IDX_ICUN = ROT_IDX["ICU N"]
IDX_G = ROT_IDX["G"]
IDX_CARDIO = ROT_IDX["CARDIO"]
IDX_ANESTHESIA = ROT_IDX["ELECTIVE"]  # Anesthesia track TYs just do ELECTIVE at year-end
IDX_TY_CLINIC = ROT_IDX["TY CLINIC"]
IDX_ICUH = ROT_IDX["ICU H"]

# Core Elective Categories (Cumulative)
CORE_ELECTIVES = {
    "CARDIO": [ROT_IDX["CARDIO"]],
    "NEURO": [ROT_IDX["NEURO"]],
    "GERIATRICS": [ROT_IDX["GERIATRICS"]],
    "ID": [ROT_IDX["ID"]],
    "ED": [ROT_IDX["ED"]],
}
# Both CLINIC and CLINIC * count toward required; overflow beyond required counts as elective
CLINIC_ALL_IDX = [ROT_IDX["CLINIC"], ROT_IDX["CLINIC *"]]
CLINIC_MIN_PER_WEEK = 11
CLINIC_MAX_PER_WEEK = 12
MAX_COHORT_SIZE = 12


def _indicator(model, var, idx, name=""):
    b = model.NewBoolVar(name)
    model.Add(var == idx).OnlyEnforceIf(b)
    model.Add(var != idx).OnlyEnforceIf(b.Not())
    return b


def _indicator_in(model, var, idx_list, name=""):
    if len(idx_list) == 1:
        return _indicator(model, var, idx_list[0], name)
    eqs = [_indicator(model, var, i, "") for i in idx_list]
    b = model.NewBoolVar(name)
    model.Add(sum(eqs) >= 1).OnlyEnforceIf(b)
    model.Add(sum(eqs) == 0).OnlyEnforceIf(b.Not())
    return b


def solve(
    residents: List[dict],
    requirements_by_pgy: Dict[str, List[dict]],
    completions_by_resident: Dict[int, Dict[str, int]],
    vacation_requests: List[dict],
    cohort_defs: List[dict] = None,
    july_weeks: List[int] = None,
    ramirez_until_week: int = 7,
    time_limit: int = 300,
    random_seed: Optional[int] = None,
    relax_vacation_blocks: bool = False,
    relax_geriatrics_coverage: bool = False,
) -> Tuple[Optional[Dict[int, Dict[int, str]]], str, List[str]]:
    """
    residents: [{id, name, pgy, is_senior, is_intern, cohort_id, constraints_json}]
    requirements_by_pgy: {pgy: [{category, required_weeks, counts_as}]}
    completions_by_resident: {resident_id: {category: weeks}}
    vacation_requests: [{resident_id, start_week, length_weeks, hard_lock}]
    cohort_defs: [{cohort_id, clinic_weeks}]
    """
    july_weeks = july_weeks or [1, 2, 3, 4]
    model = cp_model.CpModel()
    N = len(residents)
    weeks = list(range(1, 53))
    res_by_idx = {i: r for i, r in enumerate(residents)}
    senior_idxs = [i for i, r in enumerate(residents) if r["is_senior"]]
    intern_idxs = [i for i, r in enumerate(residents) if r["is_intern"]]
    # Sanity check: ensure these are disjoint and cover all residents active in coverage
    all_cov_idxs = set(senior_idxs) | set(intern_idxs)
    if len(all_cov_idxs) != N:
        # Some residents missing? 
        pass

    total_deficit = []
    together_bonus = []
    change_cost = []
    
    assign = {}
    for r in range(N):
        for w in weeks:
            assign[(r, w)] = model.NewIntVar(0, N_ROT - 1, f"a_{r}_{w}")

    is_on = {}

    def get_ind(r, w, idx):
        key = (r, w, idx)
        if key not in is_on:
            is_on[key] = _indicator(model, assign[(r, w)], idx, "")
        return is_on[key]

    def get_ind_set(r, w, idx_list, tag=""):
        key = (r, w, tuple(idx_list))
        if key not in is_on:
            is_on[key] = _indicator_in(model, assign[(r, w)], idx_list, f"{tag}_{r}_{w}")
        return is_on[key]

    # 1. Vacation: 4 weeks per resident, STRICTLY in two 2-week blocks (non-negotiable).
    for r in range(N):
        vac_bools = [get_ind(r, w, IDX_VAC) for w in weeks]
        model.Add(sum(vac_bools) == 4)
        # No isolated 1-week vacations. Forces blocks of 2+ weeks.
        for w in range(52):
            if w == 0:
                model.Add(vac_bools[0] <= vac_bools[1])
            elif w == 51:
                model.Add(vac_bools[51] <= vac_bools[50])
            else:
                model.Add(vac_bools[w] <= vac_bools[w-1] + vac_bools[w+1])
        # Prevent 3-week or 4-week blocks — force exactly 2+2 split
        for w in range(50):
            model.Add(sum(vac_bools[w:w+3]) <= 2)

        # FIX 2: Minimum ~3 months between vacation blocks.
        # In any 14-week window, at most 2 vacation weeks (one block).
        # This forces the two 2-week blocks to be ≥12 weeks apart.
        for s in range(52 - 13):
            model.Add(sum(vac_bools[s:s + 14]) <= 2)

        # FIX: No vacation during the holiday weeks (26 & 27). 
        model.Add(vac_bools[25] == 0) # Week 26
        model.Add(vac_bools[26] == 0) # Week 27

    # 2. Vacation requests: Block A (2 options) + Block B (2 options); solver picks best fit.
    # Incoming interns (placeholders) have no requests—solver places their vacation freely.
    vac_by_ri = {}
    for vreq in vacation_requests:
        ri = next((i for i, res in enumerate(residents) if res["id"] == vreq["resident_id"]), None)
        if ri is None:
            continue
        vac_by_ri[ri] = vreq

    for vreq in vacation_requests:
        for start, length in vreq.get("hard_locks", []):
            ri = next((i for i, res in enumerate(residents) if res["id"] == vreq["resident_id"]), None)
            if ri is None:
                continue
            for w in range(start, start + length):
                if 1 <= w <= 52:
                    # BLOCK: vacation cannot be on holiday weeks
                    if w in [26, 27]:
                        continue
                    model.Add(assign[(ri, w)] == IDX_VAC)

    def add_block_options(ri, options, tag):
        """Constrain resident ri to take 2 weeks vacation in one of the given start-week options."""
        if not options:
            return
        # FILTER: start weeks that would make week 26 or 27 a vacation week
        # (w, w+1) must not be 26 or 27. 
        # So start cannot be 25, 26, or 27.
        valid_opts = [w for w in options if w not in [25, 26, 27]]
        if not valid_opts:
            return
        
        opts = sorted(set(w for w in valid_opts if 1 <= w <= 51))
        choose = [model.NewBoolVar(f"vac_{tag}_opt{i}_{ri}") for i in range(len(opts))]
        model.Add(sum(choose) == 1)
        for i, start in enumerate(opts):
            for w in range(start, min(start + 2, 53)):
                if 1 <= w <= 52:
                    model.Add(assign[(ri, w)] == IDX_VAC).OnlyEnforceIf(choose[i])

    if not relax_vacation_blocks:
        for ri, vreq in vac_by_ri.items():
            add_block_options(ri, vreq.get("block_a_options", []), "a")
            add_block_options(ri, vreq.get("block_b_options", []), "b")

    # 3. Coverage (Strict Team Counts)
    # 3. Coverage (Strict Team Counts)
    for floor_idx in FLOOR_ABCD:
        for w in weeks:
            sr = [get_ind(r, w, floor_idx) for r in senior_idxs]
            jr = [get_ind(r, w, floor_idx) for r in intern_idxs]
            
            if w in [26, 27]:
                # Holiday: Support from PGY3s allowed to count toward "intern" slots
                # if we have interns who are off.
                model.Add(sum(sr) + sum(jr) == 3)
                model.Add(sum(sr) >= 1)
            else:
                model.Add(sum(sr) == 1) # Exactly 1 senior per floor team
                model.Add(sum(jr) == 2) # Exactly 2 interns per floor team

    for w in weeks:
        # ICU Day
        sr = [get_ind_set(r, w, ICU_DAY, "icu") for r in senior_idxs]
        jr = [get_ind_set(r, w, ICU_DAY, "icu") for r in intern_idxs]
        if w in [26, 27]:
            model.Add(sum(sr) + sum(jr) == 4)
            model.Add(sum(sr) >= 1)
        else:
            model.Add(sum(sr) == 2)
            model.Add(sum(jr) == 2)

    # Night shifts and special teams: ICU Night, NF, Swing, Team G
    for w in weeks:
        jr_nf = [get_ind(r, w, IDX_NF) for r in intern_idxs]
        jr_icun = [get_ind(r, w, IDX_ICUN) for r in intern_idxs]
        jr_swing = [get_ind(r, w, IDX_SWING) for r in intern_idxs]
        
        sr_nf = [get_ind(r, w, IDX_NF) for r in senior_idxs]
        sr_icun = [get_ind(r, w, IDX_ICUN) for r in senior_idxs]
        sr_swing = [get_ind(r, w, IDX_SWING) for r in senior_idxs]
        sr_g = [get_ind(r, w, IDX_G) for r in senior_idxs]

        if w in [26, 27]:
            # Combined total for each team (usually 2 people)
            model.Add(sum(jr_nf) + sum(sr_nf) == 2)
            model.Add(sum(jr_icun) + sum(sr_icun) == 2)
            model.Add(sum(jr_swing) + sum(sr_swing) == 2)
            # FIX: Team G is NOT scheduled on holiday weeks.
            model.Add(sum(sr_g) == 0)
        else:
            model.Add(sum(jr_nf) == 1)
            model.Add(sum(jr_icun) == 1)
            model.Add(sum(jr_swing) == 1)
            model.Add(sum(sr_nf) == 1)
            model.Add(sum(sr_icun) == 1)
            model.Add(sum(sr_swing) == 1)
            # FIX: Team G is PREFERRED (rewarded) but can be turned off if seniors are capped.
            is_g_active = model.NewBoolVar(f"is_all_g_on_{w}")
            model.Add(sum(sr_g) == is_g_active)
            # 300k reward for having Team G active
            total_deficit.append(is_g_active.Not() * 300000)

        # No interns on Team G (Senior only)
        jr_g = [get_ind(r, w, IDX_G) for r in intern_idxs]
        model.Add(sum(jr_g) == 0)

    IDX_GERIATRICS = ROT_IDX["GERIATRICS"]
    IDX_NEURO = ROT_IDX["NEURO"]
    if not relax_geriatrics_coverage:
        for w in weeks:
            # Senior Geriatrics coverage
            sr_geri_bools = [get_ind(r, w, IDX_GERIATRICS) for r in senior_idxs]
            has_geri = model.NewBoolVar(f"has_geri_{w}")
            model.Add(sum(sr_geri_bools) >= 1).OnlyEnforceIf(has_geri)
            model.Add(sum(sr_geri_bools) == 0).OnlyEnforceIf(has_geri.Not())
            total_deficit.append(has_geri.Not() * 1000000) 
            
            # Senior Neuro coverage
            sr_neuro_bools = [get_ind(r, w, IDX_NEURO) for r in senior_idxs]
            has_neuro = model.NewBoolVar(f"has_neuro_{w}")
            model.Add(sum(sr_neuro_bools) >= 1).OnlyEnforceIf(has_neuro)
            model.Add(sum(sr_neuro_bools) == 0).OnlyEnforceIf(has_neuro.Not())
            total_deficit.append(has_neuro.Not() * 1000000)

    for r in intern_idxs:
        for w in weeks:
            model.Add(assign[(r, w)] != IDX_G)

    # 3b. Geriatrics: SENIORS ONLY (PGY2/PGY3). Interns cannot do Geriatrics.
    IDX_GERI = ROT_IDX["GERIATRICS"]
    for r in intern_idxs:
        for w in weeks:
            model.Add(assign[(r, w)] != IDX_GERI)

    # FIX 1: TY CLINIC and GEN SURG restriction.
    # GEN SURG is ONLY for TY Anesthesia.
    # TY CLINIC is ONLY for TY residents.
    # TY residents MUST NOT do regular IM CLINIC.
    IDX_GEN_SURG = ROT_IDX["GEN SURG"]
    for r in range(N):
        res = residents[r]
        pgy = res.get("pgy")
        track = res.get("track") or ""
        is_ty = (pgy == "TY" or res.get("is_ty", False))
        is_ty_anesthesia = (is_ty and track == "anesthesia")

        for w in weeks:
            # 1a. TY CLINIC restriction
            if not is_ty:
                model.Add(assign[(r, w)] != IDX_TY_CLINIC)
            
            # 1b. GEN SURG restriction (ONLY for Anesthesia TYs)
            # General Surgery is strictly for anesthesia track TYs per user rule.
            if not is_ty_anesthesia:
                model.Add(assign[(r, w)] != IDX_GEN_SURG)

            # 1c. TYs cannot do standard IM CLINIC
            if is_ty:
                model.Add(assign[(r, w)] != ROT_IDX["CLINIC"])
                model.Add(assign[(r, w)] != ROT_IDX["CLINIC *"])

    # 4. ED: max 3, no one in July
    for w in weeks:
        ed_all = [_indicator(model, assign[(r, w)], IDX_ED, "") for r in range(N)]
        model.Add(sum(ed_all) <= 3)
        if w in july_weeks:
            model.Add(sum(ed_all) == 0)

    # 5. Ramirez & PGY-2 Delayed Start
    for r in range(N):
        res = residents[r]
        pgy = res["pgy"]
        
        # PGY-1 Ramirez Rule: No Cardio until mid-August
        if pgy == "PGY1" and not res.get("is_ty", False):
            cj = res.get("constraints_json") or {}
            until = cj.get("no_cardio_before_week", ramirez_until_week)
            for w in range(1, until + 1):
                model.Add(assign[(r, w)] != IDX_CARDIO)
        
        # PGY-2 Delayed Start Rule: No Floors/ICU Week 1
        if pgy == "PGY2":
            for w in range(1, 2):
                for idx in FLOOR_ABCD + [IDX_G, IDX_NF, IDX_SWING] + ICU_DAY + [IDX_ICUN]:
                     model.Add(assign[(r, w)] != idx)

    # 6. ICU/Night caps: max 8 weeks/year, max 16 total, strictly max 2 consecutive
    ICU_TOTAL_IDX = ICU_DAY + [IDX_ICUN]
    for r in range(N):
        night_bools = [get_ind_set(r, w, NIGHT_IDX, "n") for w in weeks]
        model.Add(sum(night_bools) <= 8)
        prior_nights = completions_by_resident.get(residents[r]["id"], {}).get("NF", 0) + completions_by_resident.get(residents[r]["id"], {}).get("ICU_NIGHT", 0)
        model.Add(prior_nights + sum(night_bools) <= 16)
        
        # Max 2 consecutive nights (hard)
        for s in range(51):
            model.Add(sum(night_bools[s:s+3]) <= 2)
            
        # Max 2 consecutive ICU (hard)
        icu_bools = [get_ind_set(r, w, ICU_TOTAL_IDX, "icu_tot") for w in weeks]
        for s in range(51):
            model.Add(sum(icu_bools[s:s+3]) <= 2)

    # 6b. Max 4 consecutive FLOOR weeks (A/B/C/D/G/NF/SWING).
    ALL_FLOOR_IDX = FLOOR_ABCD + [IDX_G, IDX_NF, IDX_SWING]
    for r in range(N):
        floor_bools = [get_ind_set(r, w, ALL_FLOOR_IDX, "fl") for w in weeks]
        for s in range(49):  # 52 - 4 + 1
            model.Add(sum(floor_bools[s:s + 5]) <= 4)

    # 6c. Soft consecutive limits on the SAME floor team (A, B, C, D, or G).
    # Team G (Seniors): Preferred 2 weeks max consecutively.
    # ABCD Seniors: 2 weeks max. ABCD Interns: 4 weeks max.
    for r in range(N):
        pgy_str = residents[r].get("pgy", "PGY1")
        is_sr = (pgy_str in ["PGY2", "PGY3"])
        
        # TEAM G: Soft 2-week cap (rewarding diversity)
        g_bools = [get_ind(r, w, IDX_G) for w in weeks]
        for s in range(50):
            excess_g = model.NewBoolVar(f"g_exc_{r}_{s}")
            model.Add(sum(g_bools[s:s+3]) >= 3).OnlyEnforceIf(excess_g)
            total_deficit.append(excess_g * 1000000) # Heavy penalty for >2 consecutive G weeks

        # ABCD TEAMS
        limit = 2 if is_sr else 4
        for team_idx in FLOOR_ABCD:
            team_bools = [get_ind(r, w, team_idx) for w in weeks]
            for s in range(52 - limit):
                model.Add(sum(team_bools[s:s + limit + 1]) <= limit)

    # 6d. STAGGER ELECTIVES & CLINIC (SOFT)
    # PGY1/2: Max 2-3 consecutive weeks of Electives to maintain balanced pace.
    # PGY3: Flexible (they should finish early).
    ANY_ELECTIVE_IDX = [ROT_IDX["ELECTIVE"], ROT_IDX["CARDIO"], ROT_IDX["ID"], 
                        ROT_IDX["NEURO"], ROT_IDX["GERIATRICS"], ROT_IDX["GEN SURG"]]
    
    for r in range(N):
        pgy_str = residents[r].get("pgy", "PGY1")
        is_pgy3 = (pgy_str == "PGY3")
        
        # Elective staggering for PGY1/2
        if not is_pgy3:
            el_bools = [get_ind_set(r, w, ANY_ELECTIVE_IDX, "el_stag") for w in weeks]
            for s in range(49):
                # Triple-elective penalty
                excess_3 = model.NewBoolVar(f"el_exc3_{r}_{s}")
                model.Add(sum(el_bools[s:s+3]) >= 3).OnlyEnforceIf(excess_3)
                total_deficit.append(excess_3 * 500000)
                
                # Quad-elective penalty (Stricter)
                excess_4 = model.NewBoolVar(f"el_exc4_{r}_{s}")
                model.Add(sum(el_bools[s:s+4]) >= 4).OnlyEnforceIf(excess_4)
                total_deficit.append(excess_4 * 2000000)

        # 6e. STAGGER CLINIC: Favor max 2 consecutive CLINIC weeks.
        clinic_bool_list = [get_ind_set(r, w, CLINIC_ALL_IDX, "cl") for w in weeks]
        for s in range(50): 
            excess = model.NewBoolVar(f"cl_exc_{r}_{s}")
            model.Add(sum(clinic_bool_list[s:s+3]) >= 3).OnlyEnforceIf(excess)
            total_deficit.append(excess * 500000)

    # 6f. Global Staggering Safety Net (Softened to avoid INFEASIBLE)
    STAGGER_GROUPS = [
        ("FLOOR", ALL_FLOOR_IDX),
        ("NIGHTS", NIGHT_IDX),
    ]
    for r in range(N):
        for name, idx_list in STAGGER_GROUPS:
            group_bools = [get_ind_set(r, w, idx_list, f"stag_{name}") for w in weeks]
            for s in range(47): 
                excess = model.NewBoolVar(f"glob_exc_{r}_{s}_{name}")
                model.Add(sum(group_bools[s:s+6]) >= 6).OnlyEnforceIf(excess)
                total_deficit.append(excess * 5000000)

    # Block Stability: Soft preference for same rotation in consecutive weeks.
    # SIMPLIFIED: just track changes in the objective, no intermediate variables.
    # This massively reduces the model size and speeds up solving.
    change_cost = []
    for r_idx in range(N):
        for w in range(1, 52):
            diff = model.NewBoolVar(f"ch_{r_idx}_{w}")
            model.Add(assign[(r_idx, w)] != assign[(r_idx, w + 1)]).OnlyEnforceIf(diff)
            model.Add(assign[(r_idx, w)] == assign[(r_idx, w + 1)]).OnlyEnforceIf(diff.Not())
            change_cost.append(diff)

    # 7. Requirements (remaining = required - completed)
    # NF counts as FLOORS. SWING counts as NF/Floor or ICUN. ICU days/nights interchangeable.
    REQ_TO_IDX = {
        "ICU": ICU_DAY + [IDX_ICUN, IDX_SWING],
        "ICU_NIGHT": [IDX_ICUN, IDX_SWING],
        "FLOORS": FLOOR_ABCD + [IDX_G, IDX_NF, IDX_SWING],
        "CLINIC": CLINIC_ALL_IDX + [IDX_TY_CLINIC],
        "CARDIO": [ROT_IDX["CARDIO"]],
        "ID": [ROT_IDX["ID"]],
        "ED": [IDX_ED],
        "NEURO": [ROT_IDX["NEURO"]],
        "NF": [IDX_NF, IDX_SWING],
        "GERIATRICS": [ROT_IDX["GERIATRICS"]],
        "GEN SURG": [ROT_IDX["GEN SURG"]],
        "ELECTIVE": [ROT_IDX["ELECTIVE"], ROT_IDX["CARDIO"],
                     ROT_IDX["ID"], ROT_IDX["NEURO"], ROT_IDX["GERIATRICS"],
                     ROT_IDX["GEN SURG"], ROT_IDX["ICU H"], IDX_TY_CLINIC],
        "TY CLINIC": [IDX_TY_CLINIC],
    }

    ty_idxs = [r for r in range(N) if residents[r].get("pgy") == "TY" or residents[r].get("is_ty", False)]

    for r_idx in range(N):
        res = residents[r_idx]
        pgy = res["pgy"]
        track = res.get("track") or ""
        is_anesthesia = (track == "anesthesia")
        
        reqs = requirements_by_pgy.get(f"{pgy}:{track}", []) or requirements_by_pgy.get(f"{pgy}:", [])
        comp = completions_by_resident.get(res["id"], {})
        
        # 7a. Special TY / Anesthesia & Neurology Logic
        if pgy == "TY":
            track_clean = (track or "").lower()
            is_anes = (track_clean == "anesthesia")
            is_neuro = (track_clean == "neurology")

            if is_anes:
                # Anesthesia: Last 4 weeks = Anesthesia (Elective)
                for w in range(49, 53):
                    model.Add(assign[(r_idx, w)] == IDX_ANESTHESIA)

            # NEURO: Only Neuro TYs rotate through Neuro. Others block it.
            if not is_neuro:
                for w in weeks:
                    model.Add(assign[(r_idx, w)] != ROT_IDX["NEURO"])
            
            # TY shared core requirements: (Use soft constraints with high penalties for solvability)
            def add_ty_soft_req(idx_set, needed, name, weight=1000000):
                # Penalty for over-scheduling core - REMOVED for speed
                # The roster is tight enough that we don't need to penalize going over, 
                # because they physically can't go much over.
                actual = sum(get_ind_set(r_idx, w, idx_set) for w in weeks)
                deficit = model.NewIntVar(0, needed, f"ty_def_{r_idx}_{name}")
                model.Add(actual + deficit >= needed)
                total_deficit.append(deficit * weight)

            # 24 Floors (User: 24 weeks of floor)
            # floors = ABCD + G + NF + SWING
            add_ty_soft_req(REQ_TO_IDX["FLOORS"], 24, "floor", weight=2000000)
            
            # 4 ICU (User: 4 ICU)
            add_ty_soft_req(REQ_TO_IDX["ICU"], 4, "icu", weight=2000000)
            
            # 4 ED (User: 4 ED)
            add_ty_soft_req([IDX_ED], 4, "ed", weight=2000000)
            
            # 4 GEN SURG (User: 4 weeks ONLY for anesthesia track TYs)
            surg_needed = 4 if is_anes else 0
            add_ty_soft_req(REQ_TO_IDX["GEN SURG"], surg_needed, "gensurg", weight=2000000)
            
            # 4 CLINIC (User: 4 Clinic)
            add_ty_soft_req([IDX_TY_CLINIC], 4, "clinic", weight=2000000)
            
            # Electives (Anesthesia: 8 weeks; Neuro: 12 weeks to offset no surgery)
            elective_needed = 8 if is_anes else 12
            add_ty_soft_req(REQ_TO_IDX["ELECTIVE"], elective_needed, "elective", weight=500)
            
            # STRESS: TYs should NOT exceed their core requirements if possible.
            # REMOVED complex penalty for speed.

            # Skip the general PGY requirements logic below for TYs
            continue

        # 7b. General PGY Requirements
        clinic_req = next((r["required_weeks"] for r in reqs if r["category"] == "CLINIC"), 0)
        clinic_comp = comp.get("CLINIC", 0)
        clinic_bools = [get_ind_set(r_idx, w, CLINIC_ALL_IDX, "cl") for w in weeks]
        clinic_sum = sum(clinic_bools)
        
        # Clinic overflow logic
        clinic_overflow = model.NewIntVar(0, 52, f"clinic_ov_{r_idx}")
        model.Add(clinic_overflow >= clinic_sum + clinic_comp - clinic_req)
        
        for req in reqs:
            cat = req["category"]
            if cat == "VACATION":
                continue
            
            req_min = req["required_weeks"]
            done = comp.get(cat, 0)
            
            # Reset history for Annual Categories (Floors, ICU, Clinic)
            # The user wants them to do the full amount each year regardless of history.
            if cat in ["FLOORS", "ICU", "CLINIC", "VACATION"]:
                done = 0
                
            needed = max(0, req_min - done)
            idx_list = REQ_TO_IDX.get(cat)
            if idx_list is None:
                continue

            cat_bools = [get_ind_set(r_idx, w, idx_list, cat) for w in weeks]
            
            # STRICT REQUIREMENTS — deficit penalty 10M per missing week
            if cat in ["FLOORS", "ICU", "CLINIC", "ED", "NEURO", "GERIATRICS", "CARDIO", "ID"]:
                deficit = model.NewIntVar(0, 52, f"def_{r_idx}_{cat}")
                model.Add(sum(cat_bools) + deficit >= needed)
                total_deficit.append(deficit * 10000000)  # 10M per missing week
                
                # SURPLUS PENALTY: Prevent residents from going way past their floor requirements
                # High priority to stop G-team bleed, but lower than mandatory coverage.
                surplus = model.NewIntVar(0, 52, f"sur_{r_idx}_{cat}")
                model.Add(sum(cat_bools) <= needed + surplus)
                if cat == "FLOORS":
                    total_deficit.append(surplus * 1000000) # 1M penalty per extra floor week

                # FIX 4: Hard cap on CORE ELECTIVE rotations.
                # Cannot exceed required_weeks. FLOORS/ICU/CLINIC are exempt (coverage needs).
                if cat in ["CARDIO", "NEURO", "GERIATRICS", "ID", "ED"]:
                    model.Add(sum(cat_bools) <= req_min)
                
                # PGY-3 Front-Loading Soft Constraint: Reward doing Floors/ICU early (Weeks 1-30)
                if pgy == "PGY3" and cat in ["FLOORS", "ICU"]:
                    late_weeks = [b for w, b in zip(weeks, cat_bools) if w > 30]
                    for b in late_weeks:
                        total_deficit.append(b * 500) # Moderate penalty for late scheduling
            else:
                # SOFT REQUIREMENTS (Electives, etc.)
                deficit = model.NewIntVar(0, 52, f"def_{r_idx}_{cat}")
                
                model.Add(sum(cat_bools) + (clinic_overflow if cat == "ELECTIVE" else 0) + deficit >= needed)
                # Higher penalty for electives too — 1M per missing week
                penalty = 1000000
                total_deficit.append(deficit * penalty)

        # 7c. Cumulative Core Electives (Cardio, Neuro, Geri, ID, ED)
        # Ensure that by graduation, these minimums are met.
        CORE_MINS_GRAD = {"CARDIO": 4, "NEURO": 2, "GERIATRICS": 2, "ID": 4, "ED": 4}
        if pgy == "PGY3":
            for cat, min_val in CORE_MINS_GRAD.items():
                done = comp.get(cat, 0)
                # Calculate how many we are adding this year
                idx_list = CORE_ELECTIVES.get(cat)
                if not idx_list:
                    idx_list = REQ_TO_IDX.get(cat)
                if not idx_list: continue
                this_year = sum(get_ind_set(r_idx, w, idx_list, f"cum_{cat}") for w in weeks)
                
                deficit = model.NewIntVar(0, min_val, f"cum_def_{r_idx}_{cat}")
                model.Add(done + this_year + deficit >= min_val)
                total_deficit.append(deficit * 20000000) # 20M - Graduation requirements are absolute priority

    # 8. Clinic: designated cohort must be present; total 10-12 (3-5 extras from any cohort)
    # Cohorts are capped at MAX_COHORT_SIZE (9), so all cohort members fit in clinic.
    cohort_defs = cohort_defs or []
    for cd in cohort_defs:
        # TYs do not attend IM clinic; they have their own clinic elsewhere.
        # So we exclude them from the cohort forcing that puts them in our resident clinic.
        coh_res = [i for i, r in enumerate(residents) if r.get("cohort_id") == cd["cohort_id"] and not r.get("is_ty")]
        if not coh_res:
            continue
        for w in cd.get("clinic_weeks", []):
            if 1 <= w <= 52:
                if w in [26, 27]:
                    continue # Holiday rules override cohort
                for r in coh_res:
                    # If TY, use TY CLINIC. Otherwise use regular IM CLINIC.
                    is_ty_res = (residents[r].get("pgy") == "TY" or residents[r].get("is_ty", False))
                    target_cl_idx = [IDX_TY_CLINIC] if is_ty_res else CLINIC_ALL_IDX
                    b = get_ind_set(r, w, target_cl_idx, "cl")
                    model.Add(b == 1)
    for w in weeks:
        if w in [26, 27]:
            continue # Holiday schedule handles clinic differently
        # TYs do not attend our clinic (they have their own elsewhere), so they don't count toward local minimums
        clinic_count = sum(get_ind_set(r, w, CLINIC_ALL_IDX, "cl") for r in range(N) if r not in ty_idxs)
        model.Add(clinic_count >= CLINIC_MIN_PER_WEEK)
        model.Add(clinic_count <= CLINIC_MAX_PER_WEEK)


    # Co-intern pairing: HARD constraint
    # If both co-interns are on floor teams (A/B/C/D) in the same week,
    # they MUST be on the same team. Non-negotiable.
    co_intern_pairs = []
    cohort_interns = {}
    for i in intern_idxs:
        cid = residents[i].get("cohort_id")
        if cid is not None:
            cohort_interns.setdefault(cid, []).append(i)
    for cid, idxs in cohort_interns.items():
        # Pair by order: (0,1), (2,3), etc.
        for p in range(0, len(idxs) - 1, 2):
            co_intern_pairs.append((idxs[p], idxs[p + 1]))

    for (i, j) in co_intern_pairs:
        for w in weeks:
            # If BOTH are on any floor team (A/B/C/D), force same assignment
            fi = get_ind_set(i, w, FLOOR_ABCD, "floor")
            fj = get_ind_set(j, w, FLOOR_ABCD, "floor")
            # assign[i,w] == assign[j,w] when both on floors
            model.Add(assign[(i, w)] == assign[(j, w)]).OnlyEnforceIf(fi, fj)

            # Same for ICU: if both on ICU day, force same assignment
            ui = get_ind_set(i, w, ICU_DAY, "icu")
            uj = get_ind_set(j, w, ICU_DAY, "icu")
            model.Add(assign[(i, w)] == assign[(j, w)]).OnlyEnforceIf(ui, uj)

    # 10. HOLIDAY SCHEDULE (Weeks 26 & 27)
    # Essential Coverage: Floors, ICU, NF, SWING, ICU N, TEAM G.
    # All others must be ICU H. Reciprocity: work one, off one.
    HOLIDAY_WEEKS = [26, 27]
    ESSENTIAL_COV_IDX = ALL_FLOOR_IDX + ICU_DAY + [IDX_ICUN]
    CLINIC_HOL_IDX = CLINIC_ALL_IDX + [IDX_TY_CLINIC]
    
    # HARD RESTRICTION: ICU H is ONLY for holiday weeks 26 & 27.
    for r in range(N):
        for w in weeks:
            if w not in HOLIDAY_WEEKS:
                model.Add(assign[(r, w)] != IDX_ICUH)

    # HARD RESTRICTION: No other rotations except Essential, Clinic, or ICU H in these weeks.
    for w in HOLIDAY_WEEKS:
        for r in range(N):
            w_is_cov = get_ind_set(r, w, ESSENTIAL_COV_IDX, f"hol_is_cov_{w}")
            w_is_cl = get_ind_set(r, w, CLINIC_HOL_IDX, f"hol_is_cl_{w}")
            w_is_off = get_ind(r, w, IDX_ICUH)
            model.Add(w_is_cov + w_is_cl + w_is_off == 1)

    for r in range(N):
        res = residents[r]
        pgy = res.get("pgy")
        comp = completions_by_resident.get(res["id"], {})
        
        # Holiday Indicators
        w1_off = get_ind(r, 26, IDX_ICUH)
        w2_off = get_ind(r, 27, IDX_ICUH)

        # MANDATORY: No one works both weeks.
        model.Add(w1_off + w2_off >= 1)

        # 1. Non-PGY3s: MUST work exactly one week.
        if pgy != "PGY3":
            model.Add(w1_off + w2_off == 1)
        else:
            # 2. PGY3: Can work 0 or 1 weeks. 
            # Weighted penalty for working based on core completion progress.
            # PGY-3s who have finished most core (Floor, ICU, Nights) are penalized LESS.
            core_weeks = comp.get("FLOORS", 0) + comp.get("ICU", 0) + comp.get("NF", 0)
            # score = 0 (finished nothing) to ~40+ (finished everything)
            # We want higher core_weeks to have LOWER penalty.
            pgy3_work_penalty = 10000000 - (core_weeks * 200000)
            
            w1_any_work = model.NewBoolVar(f"pgy3_w1_work_{r}")
            model.Add(w1_off == 0).OnlyEnforceIf(w1_any_work)
            model.Add(w1_off == 1).OnlyEnforceIf(w1_any_work.Not())
            total_deficit.append(w1_any_work * pgy3_work_penalty)
            
            w2_any_work = model.NewBoolVar(f"pgy3_w2_work_{r}")
            model.Add(w2_off == 0).OnlyEnforceIf(w2_any_work)
            model.Add(w2_off == 1).OnlyEnforceIf(w2_any_work.Not())
            total_deficit.append(w2_any_work * pgy3_work_penalty)
            
    # Holiday Clinic Cap: Max 5 per week (Week 26, 27)
    clinic_total_idx = CLINIC_ALL_IDX + [IDX_TY_CLINIC]
    for w in HOLIDAY_WEEKS:
        clinic_holiday = [get_ind_set(r, w, clinic_total_idx, f"hol_cl_cap_{w}") for r in range(N)]
        model.Add(sum(clinic_holiday) <= 5)

    # Objective: minimize deficits (highest priority), then minimize rotation changes (tie-breaker)
    model.Minimize(
        sum(total_deficit)
        + sum(change_cost)  # change_cost items are just 0/1 booleans, so they're tie-breakers
    )

    # Solve
    # Callback to log progress
    class ProgressPrinter(cp_model.CpSolverSolutionCallback):
        def __init__(self, limit):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.__limit = limit
            self.__solution_count = 0

        def on_solution_callback(self):
            self.__solution_count += 1
            print(f"Solution {self.__solution_count} found: objective value = {self.ObjectiveValue()}")
            if self.__solution_count >= self.__limit:
                self.StopSearch()

    solver = cp_model.CpSolver()
    # Performance Optimization: Use half of available cores to avoid freezing the PC
    # 8 cores was too aggressive and starved the OS. 4 is safer.
    solver.parameters.num_search_workers = 4
    
    
    # Priority: Find a feasible solution quickly
    # solver.parameters.search_branching = cp_model.AUTOMATIC_SEARCH # Default is automatic
    
    # Quick timeout to prevent 502/Gateway Timeouts on frontend
    # Increased default to 300 seconds as the 22-intern roster is very tight.
    lim = time_limit if time_limit > 0 else 300
    solver.parameters.max_time_in_seconds = float(lim)
    
    if random_seed is not None:
        solver.parameters.random_seed = random_seed

    status = solver.Solve(model)
    conflicts = []

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        assignments = {}
        for r in range(N):
            rid = residents[r]["id"]
            assignments[rid] = {}
            for w in weeks:
                idx = int(solver.Value(assign[(r, w)]))
                assignments[rid][w] = ROT_CODES[idx]
        st = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
        return assignments, st, conflicts

    conflicts.append(solver.StatusName(status))
    for v in vacation_requests:
        if v.get("hard_lock"):
            conflicts.append(f"Hard lock: resident {v['resident_id']} weeks {v['start_week']}-{v['start_week']+v.get('length_weeks',2)-1}")
    return None, solver.StatusName(status), conflicts
