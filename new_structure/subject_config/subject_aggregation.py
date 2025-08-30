"""
Subject Aggregation Configuration

This module defines how independent subjects are grouped into composite subjects
for display purposes while maintaining independent upload functionality.
"""

# Composite subject configuration
COMPOSITE_SUBJECT_MAPPING = {
    'ENGLISH': {
        'components': ['English Grammar', 'English Composition'],
        'abbreviations': ['GRAM', 'COMP'],
        'weights': [1.0, 1.0],  # Equal weight for averaging
        'max_marks': 100
    },
    'KISWAHILI': {
        'components': ['Kiswahili Lugha', 'Kiswahili Insha'],
        'abbreviations': ['LUGHA', 'INSHA'],
        'weights': [1.0, 1.0],  # Equal weight for averaging
        'max_marks': 100
    }
}

def get_composite_subjects():
    """Return list of composite subject names."""
    return list(COMPOSITE_SUBJECT_MAPPING.keys())

def get_component_subjects(composite_name):
    """Return list of component subjects for a composite subject."""
    return COMPOSITE_SUBJECT_MAPPING.get(composite_name, {}).get('components', [])

def get_composite_max_marks(composite_name):
    """Return maximum marks for a composite subject."""
    return COMPOSITE_SUBJECT_MAPPING.get(composite_name, {}).get('max_marks', 100)

def get_component_weight(composite_name, component_name):
    """Return weight for a specific component in a composite subject."""
    config = COMPOSITE_SUBJECT_MAPPING.get(composite_name, {})
    components = config.get('components', [])
    weights = config.get('weights', [])
    
    if component_name in components:
        index = components.index(component_name)
        return weights[index] if index < len(weights) else 1.0
    return 1.0

def get_component_abbreviations(composite_name):
    """Return abbreviations for components of a composite subject."""
    return COMPOSITE_SUBJECT_MAPPING.get(composite_name, {}).get('abbreviations', [])

def is_composite_subject(subject_name):
    """Check if a subject is a composite subject."""
    return subject_name in COMPOSITE_SUBJECT_MAPPING

def is_component_subject(subject_name):
    """Check if a subject is a component of any composite subject."""
    for composite_config in COMPOSITE_SUBJECT_MAPPING.values():
        if subject_name in composite_config.get('components', []):
            return True
    return False

def get_composite_for_component(component_name):
    """Get the composite subject name for a given component."""
    for composite_name, config in COMPOSITE_SUBJECT_MAPPING.items():
        if component_name in config.get('components', []):
            return composite_name
    return None
