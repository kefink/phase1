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

# Assessment types
ASSESSMENT_TYPES = [
    'End Term',
    'Mid Term',
    'CAT 1',
    'CAT 2'
]

# Terms
TERMS = [
    'Term 1',
    'Term 2',
    'Term 3'
]
