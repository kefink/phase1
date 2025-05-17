"""
Constants used throughout the application.
"""

# Educational level mapping
educational_level_mapping = {
    'lower_primary': ['PP1', 'PP2', 'Grade 1', 'Grade 2', 'Grade 3'],
    'upper_primary': ['Grade 4', 'Grade 5', 'Grade 6'],
    'junior_secondary': ['Grade 7', 'Grade 8', 'Grade 9']
}

# Performance categories
PERFORMANCE_CATEGORIES = {
    'Exceeding Expectation': (80, 100),
    'Meeting Expectation': (65, 79),
    'Approaching Expectation': (50, 64),
    'Below Expectation': (0, 49)
}

# Assessment types and terms are now dynamically loaded from the database
# instead of being hardcoded here
