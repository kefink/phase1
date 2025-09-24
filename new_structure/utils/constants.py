"""
Constants and helpers used throughout the application.

This module centralizes the canonical definition and ordering of educational
levels and their grade ranges for consistent usage across the system.
"""

# Canonical order of education levels for UI and filters
EDUCATION_LEVELS_ORDER = [
    'pre_primary',         # PP1–PP2
    'lower_primary',       # Grade 1–3
    'upper_primary',       # Grade 4–6
    'junior_secondary',    # Grade 7–9
    'senior_secondary',    # Grade 10–12
]

# Canonical mapping: level -> allowed grade names
# Note: DB may still store PP1/PP2 with lower_primary. This mapping is for UI.
educational_level_mapping = {
    'pre_primary': ['PP1', 'PP2'],
    'lower_primary': ['Grade 1', 'Grade 2', 'Grade 3'],
    'upper_primary': ['Grade 4', 'Grade 5', 'Grade 6'],
    'junior_secondary': ['Grade 7', 'Grade 8', 'Grade 9'],
    'senior_secondary': ['Grade 10', 'Grade 11', 'Grade 12'],
}

def get_education_level_for_grade_name(grade_name: str) -> str:
    """Return the canonical education level code for a grade name.

    Examples:
    - 'PP1' -> 'pre_primary'
    - 'Grade 2' -> 'lower_primary'
    - 'Grade 9' -> 'junior_secondary'
    - 'Grade 12' -> 'senior_secondary'
    Returns empty string when unknown.
    """
    try:
        if not grade_name:
            return ''
        name = str(grade_name).strip()
        if name.upper() in ('PP1', 'PP2'):
            return 'pre_primary'
        if name.lower().startswith('grade'):
            parts = name.split()
            if len(parts) == 2 and parts[1].isdigit():
                n = int(parts[1])
                if 1 <= n <= 3:
                    return 'lower_primary'
                if 4 <= n <= 6:
                    return 'upper_primary'
                if 7 <= n <= 9:
                    return 'junior_secondary'
                if 10 <= n <= 12:
                    return 'senior_secondary'
        # Some DBs may store just the number
        if name.isdigit():
            n = int(name)
            if 1 <= n <= 3:
                return 'lower_primary'
            if 4 <= n <= 6:
                return 'upper_primary'
            if 7 <= n <= 9:
                return 'junior_secondary'
            if 10 <= n <= 12:
                return 'senior_secondary'
        return ''
    except Exception:
        return ''

def order_levels(levels: list) -> list:
    """Order a list of education level codes by the canonical order.

    Unknown levels are appended at the end in their original order.
    """
    if not levels:
        return []
    seen = set()
    # Keep only unique while preserving original order
    unique_levels = []
    for lv in levels:
        if lv not in seen:
            unique_levels.append(lv)
            seen.add(lv)
    ordered = [lv for lv in EDUCATION_LEVELS_ORDER if lv in unique_levels]
    tail = [lv for lv in unique_levels if lv not in EDUCATION_LEVELS_ORDER]
    return ordered + tail

# Performance categories
PERFORMANCE_CATEGORIES = {
    'Exceeding Expectation': (80, 100),
    'Meeting Expectation': (65, 79),
    'Approaching Expectation': (50, 64),
    'Below Expectation': (0, 49)
}

# Assessment types and terms are now dynamically loaded from the database
# instead of being hardcoded here
