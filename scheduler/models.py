"""
Data models for the AutoScheduler system.
All structures grounded in the actual "2025 Updated Schedule - Copy 2026.xlsx" workbook.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Resident:
    """Resident identity and metadata, extracted from SCHEDULE rows 4..56."""
    name: str
    pgy: int                         # 1, 2, or 3
    is_ty: bool = False
    cohort_id: Optional[str] = None  # "Cohort 1" .. "Cohort 5"; None for TYs
    track: Optional[str] = None      # e.g. "Anesthesia"
    notes: Optional[str] = None
    row_index: Optional[int] = None  # SCHEDULE sheet row (4..56)

    @property
    def is_senior(self) -> bool:
        return self.pgy >= 2 and not self.is_ty

    @property
    def is_intern(self) -> bool:
        return self.pgy == 1 or self.is_ty


@dataclass
class Requirement:
    """Required weeks per PGY level and category."""
    pgy: str               # "PGY1", "PGY2", "PGY3", "TY"
    category: str           # matches counter column header in BD..CD
    required_weeks: int
    min_weeks: Optional[int] = None
    max_weeks: Optional[int] = None
    is_mandatory: bool = False # If Y, solver will fail if not met
    notes: Optional[str] = None


@dataclass
class VacationRequest:
    """Vacation request from the PD data-entry sheet."""
    resident_name: str
    pgy: str
    request_type: str       # "VAC_BLOCK_1" or "VAC_BLOCK_2"
    start_week: int         # 1..52
    length_weeks: int       # default 2
    priority: int = 3       # 1..5  (1 = highest)
    hard_lock: bool = False # Y = must honor
    comments: Optional[str] = None


@dataclass
class CoverageRule:
    """Weekly staffing obligation – one row per rotation pool."""
    rotation_pool: str          # e.g. "FLOOR_A", "ICU_DAY", "NF"
    required_per_week: int      # number of units needed
    senior_per_unit: int
    intern_per_unit: int
    notes: Optional[str] = None


@dataclass
class CohortDef:
    """Cohort definition for clinic 4+1 cadence."""
    cohort_id: str                      # "Cohort 1" .. "Cohort 5"
    clinic_weeks: List[int] = field(default_factory=list)   # explicit week list
    target_intern_count: int = 2        # for next-year planning
    notes: Optional[str] = None


@dataclass
class SolverConfig:
    """Global solver parameters defined in Excel."""
    max_nights_per_year: int = 8
    max_consecutive_nights: int = 4
    ed_cap_per_week: int = 3
    ramirez_forbidden_until_week: int = 7
    july_weeks: List[int] = field(default_factory=lambda: [1, 2, 3, 4])
    vacation_weeks_per_resident: int = 4
    min_working_residents: int = 21


@dataclass
class ScheduleContext:
    """All parsed data needed by the solver."""
    residents: List[Resident]
    requirements: List[Requirement]
    vacation_requests: List[VacationRequest]
    coverage_rules: List[CoverageRule]
    cohort_defs: List[CohortDef]
    config: SolverConfig = field(default_factory=SolverConfig)
    resident_row_map: Dict[str, int] = field(default_factory=dict)
    week_count: int = 52
    random_seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Counter columns in BD..CD (col 56..82) — the SCHEDULE formulas
# These map 1-to-1 with the header labels in row 1.
# ---------------------------------------------------------------------------
COUNTER_COLUMNS = {
    56: "CARDIO",
    57: "CLINIC",
    58: "ED",
    59: "FLOORS",
    60: "ICU",
    61: "ICU E",
    62: "ICU N",
    63: "ID",
    64: "NEURO",
    65: "NF",
    66: "SWING",
    67: "VACATION",
    68: "SUB-TOTAL",
    69: "PALLIATIVE",
    70: "GERIATRIC",
    71: "GS / GI",
    72: "HEM/ONC",
    73: "PAIN MANGEMENT",  # header typo in workbook; formula counts IR RADIOLOGY
    74: "RHEUMA",
    75: "ENDO",
    76: "PLASTIC",
    77: "PULM",
    78: "SICU",
    79: "DERMATOLOGY",
    80: "NEPHRO",
    81: "SUB-TOTAL2",
    82: "TOTAL",
}

# All *actual* rotation codes observed in the workbook's D..BC cells
ALL_ROTATION_CODES = sorted([
    "A", "ANESTHESIA", "B", "C", "CARDIO", "CARDIO *", "CARDIO*",
    "CLINIC", "CLINIC *", "CLINIC*", "D", "DERMATOLOGY", "ED",
    "ENDO", "ENDO *", "G", "GERIATRIC", "GERIATRIC 2", "GI", "GI *",
    "HEM/ONC", "HEM/ONC *", "ICU", "ICU E", "ICU H", "ICU H*",
    "ICU N", "ID", "ID *", "ID*", "NEPHRO", "NEPHRO *", "NEURO",
    "NEURO *", "NF", "PAIN MANAGEMENT", "PAIN MANAGEMENT *",
    "PALLIATIVE", "PALLIATIVE *", "PLASTIC", "PULM", "PULM *",
    "RHEUMA", "RHEUMA *", "SICU", "SWING", "URGENT CARE",
    "URGENT CARE *", "VACATION",
])

# Codes the solver may assign (subset used for auto-scheduling)
SOLVER_ROTATION_CODES = [
    # Floors
    "A", "B", "C", "D", "G",
    # ICU family
    "ICU", "ICU E", "ICU N",
    # Nights / coverage
    "NF", "SWING",
    # Clinic
    "CLINIC", "CLINIC *",
    # Mandatory rotations
    "ED", "CARDIO", "CARDIO-RAM", "CARDIO-HCA",
    "ID", "NEURO",
    # Vacation
    "VACATION",
    # Electives (solver may place if requirements demand)
    "PALLIATIVE", "GERIATRIC", "GI", "HEM/ONC",
    "ENDO", "RHEUMA", "PULM", "SICU", "DERMATOLOGY", "NEPHRO",
    "PLASTIC", "ANESTHESIA", "PAIN MANAGEMENT",
]

# Map rotation code → which counter column (BD..CD header) it feeds
# Derived from the actual COUNTIF formulas in the workbook
CODE_TO_COUNTER = {
    "A": "FLOORS", "B": "FLOORS", "C": "FLOORS", "D": "FLOORS", "G": "FLOORS",
    "ICU": "ICU", "ICU E": "ICU E", "ICU H": "ICU",   # ICU H not counted but treat as ICU
    "ICU H*": "ICU", "ICU N": "ICU N",
    "NF": "NF", "SWING": "SWING",
    "CLINIC": "CLINIC", "CLINIC *": "CLINIC", "CLINIC*": "CLINIC",
    "URGENT CARE": "CLINIC", "URGENT CARE *": "CLINIC",
    "ED": "ED",
    "CARDIO": "CARDIO", "CARDIO *": "CARDIO", "CARDIO*": "CARDIO",
    "CARDIO E": "CARDIO", "CARDIO E *": "CARDIO",
    "CARDIO-HCA": "CARDIO", "CARDIO-HCA *": "CARDIO",
    "CARDIO-RAM": "CARDIO", "CARDIO-RAM *": "CARDIO",
    "ID": "ID", "ID *": "ID", "ID*": "ID",
    "NEURO": "NEURO", "NEURO *": "NEURO",
    "VACATION": "VACATION",
    "PALLIATIVE": "PALLIATIVE", "PALLIATIVE *": "PALLIATIVE",
    "GERIATRIC": "GERIATRIC", "GERIATRIC 2": "GERIATRIC",
    "GI": "GS / GI", "GI *": "GS / GI", "GS": "GS / GI",
    "HEM/ONC": "HEM/ONC", "HEM/ONC *": "HEM/ONC",
    "PAIN MANAGEMENT": "PAIN MANGEMENT", "PAIN MANAGEMENT *": "PAIN MANGEMENT",
    "IR RADIOLOGY": "PAIN MANGEMENT", "IR RADIOLOGY *": "PAIN MANGEMENT",
    "RHEUMA": "RHEUMA", "RHEUMA *": "RHEUMA",
    "ENDO": "ENDO", "ENDO *": "ENDO",
    "PLASTIC": "PLASTIC", "PLASTIC *": "PLASTIC",
    "PULM": "PULM", "PULM *": "PULM",
    "SICU": "SICU", "SICU *": "SICU",
    "DERMATOLOGY": "DERMATOLOGY", "DERMATOLOGY *": "DERMATOLOGY",
    "NEPHRO": "NEPHRO", "NEPHRO *": "NEPHRO",
    "ANESTHESIA": "ANESTHESIA", "ANESTHESIA *": "ANESTHESIA",
}

# Night rotations for constraint purposes
NIGHT_CODES = {"ICU N", "NF"}
NIGHT_PLUS_SWING_CODES = {"ICU N", "NF", "SWING"}
FLOOR_CODES = {"A", "B", "C", "D"}
FLOOR_PLUS_G = {"A", "B", "C", "D", "G"}
