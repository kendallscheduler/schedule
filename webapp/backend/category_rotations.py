"""Mapping of requirement categories to rotation codes (used by schedule and requirements)."""

CAT_ROTS = {
    "CLINIC": ["CLINIC", "CLINIC *", "TY CLINIC"],  # TY CLINIC for TYs, regular for IM
    "CARDIO": ["CARDIO", "CARDIO-RAM", "CARDIO-HCA"],
    "ED": ["ED"],
    "ID": ["ID"],
    "NEURO": ["NEURO"],
    "VACATION": ["VACATION"],
    "GERIATRICS": ["GERIATRICS"],
    "GEN SURG": ["GEN SURG"],
    "ELECTIVE": [
        "ELECTIVE", "CARDIO", "CARDIO-RAM", "CARDIO-HCA", "ID", "NEURO", "GERIATRICS",
        "PULMONOLOGY", "NEPHROLOGY", "PALLIATIVE", "PAIN", "RHEUMATOLOGY", "ENDOCRINOLOGY", 
        "ICU H", "GEN SURG", "TY CLINIC",
    ],
}
FLOOR_ROTS = ["A", "B", "C", "D", "G"]
ICU_ROTS = ["ICU", "ICU E", "ICU N"]


def get_categories_for_rotation(rotation_code: str) -> list[str]:
    """Return categories that this rotation counts toward."""
    out = []
    for cat in list(CAT_ROTS.keys()) + ["FLOORS", "NF", "ICU_NIGHT", "ICU", "SWING"]:
        if rotation_code in get_rotations_for_category(cat):
            out.append(cat)
    return list(dict.fromkeys(out))


def get_rotations_for_category(category: str) -> list[str]:
    """Return rotation codes that count toward this requirement category."""
    if category in CAT_ROTS:
        return CAT_ROTS[category]
    if category == "FLOORS":
        return FLOOR_ROTS + ["NF"]
    if category == "NF":
        return ["NF"]
    if category == "ICU_NIGHT":
        return ["ICU N"]
    if category == "ICU":
        return ICU_ROTS
    if category == "SWING":
        return ["SWING"]
    return []
