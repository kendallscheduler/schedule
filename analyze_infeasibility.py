
import sys
from pathlib import Path
from scheduler.parse_inputs import parse_workbook
from scheduler.models import Resident, Requirement, CoverageRule

def analyze_context(wb_path):
    print(f"Analyzing workbook: {wb_path}")
    ctx = parse_workbook(wb_path)
    
    seniors = [r for r in ctx.residents if r.is_senior]
    interns = [r for r in ctx.residents if r.is_intern]
    
    print(f"Total Residents: {len(ctx.residents)}")
    print(f"  Seniors: {len(seniors)}")
    print(f"  Interns: {len(interns)}")
    
    # Analyze Coverage vs Resources
    # Seniors needed per week:
    # 4 (Floors A-D) + 2 (ICU) + 1 (NF) + 1 (ICU Night) + 1 (Swing) = 9
    senior_needs_per_week = 9
    intern_needs_per_week = 12 # 4*2 (Floors) + 2 (ICU) + 1 (NF) + 1 (ICU Night)
    
    print(f"\nWeekly Coverage Needs:")
    print(f"  Seniors needed: {senior_needs_per_week}")
    print(f"  Interns needed: {intern_needs_per_week}")
    
    # Clinic Cohorts
    print(f"\nCohort Info:")
    for coh in ctx.cohort_defs:
        members = [r for r in ctx.residents if r.cohort_id == coh.cohort_id]
        sr_members = [r for r in members if r.is_senior]
        jr_members = [r for r in members if r.is_intern]
        print(f"  {coh.cohort_id}: {len(members)} total ({len(sr_members)} Sr, {len(jr_members)} Jr)")
        print(f"    Clinic weeks: {coh.clinic_weeks}")
        
        # Check if any week exceeds senior/intern capacity
        for w in coh.clinic_weeks:
            avail_sr = len(seniors) - len(sr_members)
            avail_jr = len(interns) - len(jr_members)
            if avail_sr < senior_needs_per_week:
                print(f"    !!! Week {w}: Only {avail_sr} seniors available, but {senior_needs_per_week} needed.")
            if avail_jr < intern_needs_per_week:
                print(f"    !!! Week {w}: Only {avail_jr} interns available, but {intern_needs_per_week} needed.")

    # Requirements Total vs Capacity
    print(f"\nRequirements from workbook:")
    for rq in ctx.requirements:
        print(f"  {rq.pgy} {rq.category}: {rq.required_weeks}")

    print(f"\nRequirement Load analysis:")
    for cat in ["ICU", "FLOORS", "NF", "ED"]:
        total_req_weeks = 0
        for res in ctx.residents:
            pgy_label = "TY" if res.is_ty else f"PGY{res.pgy}"
            match = [rq for rq in ctx.requirements if rq.pgy == pgy_label and rq.category == cat]
            if match:
                total_req_weeks += match[0].required_weeks
        
        # Capacity (approx)
        capacity = 0
        if cat == "ICU": capacity = 52 * 4 # ICU day 2+2, ICU night 1+1 (actually ICU req includes night in models.py)
        # REQ_CAT_TO_IDX in solver.py: ICU: ICU_DAY + [IDX_ICUN] -> 2+2 + 1+1 = 6 per week total
        if cat == "ICU": capacity = 52 * 6 
        if cat == "FLOORS": 
            # Senior Floor slots: ABCD(4) + G(1) + NF(1) + Swing(1) = 7
            # Intern Floor slots: ABCD(8) + NF(1) = 9
            # Total = 16
            capacity = 52 * 16 
        if cat == "NF": capacity = 52 * (1+1) # 2 per week. (Senior+Intern)
        if cat == "ED": capacity = 52 * 3 # max 3 per week
        
        print(f"  {cat}: Total Required={total_req_weeks}, Capacity={capacity}")
        if total_req_weeks > capacity:
            print(f"    !!! ERROR: Requirement ({total_req_weeks}) exceeds capacity ({capacity})")

if __name__ == "__main__":
    analyze_context("2025 Updated Schedule - Copy 2026.xlsx")
