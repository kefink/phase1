"""
Subject Aggregation Configuration

This module defines how independent subjects should be combined into composite subjects
for display in class reports while maintaining separate upload functionality.
"""

# Define composite subject mappings
# Format: "Composite Name": ["Component 1", "Component 2", ...]
COMPOSITE_SUBJECT_MAPPING = {
    "English": ["English Grammar", "English Composition"],
    "Kiswahili": ["Kiswahili Lugha", "Kiswahili Insha"],
    # Add more composite subjects as needed
    # "Science": ["Physics", "Chemistry", "Biology"],  # Example
}

# Define maximum marks for composite subjects (optional - if not specified, will sum component max marks)
COMPOSITE_MAX_MARKS = {
    "English": 100,
    "Kiswahili": 100,
    # Add more as needed
}

# Define component weightings (if components should have different weights)
# Format: "Composite Name": {"Component 1": weight, "Component 2": weight}
COMPONENT_WEIGHTS = {
    "English": {"English Grammar": 0.5, "English Composition": 0.5},
    "Kiswahili": {"Kiswahili Lugha": 0.5, "Kiswahili Insha": 0.5},
    # Equal weights by default, but can be customized
}

def get_composite_subjects():
    """Return the list of composite subject names."""
    return list(COMPOSITE_SUBJECT_MAPPING.keys())

def get_component_subjects(composite_name):
    """Return the list of component subjects for a given composite subject."""
    return COMPOSITE_SUBJECT_MAPPING.get(composite_name, [])

def get_composite_for_component(component_name):
    """Return the composite subject name for a given component subject."""
    for composite, components in COMPOSITE_SUBJECT_MAPPING.items():
        if component_name in components:
            return composite
    return None

def is_component_subject(subject_name):
    """Check if a subject is a component of a composite subject."""
    return get_composite_for_component(subject_name) is not None

def get_composite_max_marks(composite_name):
    """Get the maximum marks for a composite subject."""
    return COMPOSITE_MAX_MARKS.get(composite_name, 100)  # Default to 100

def get_component_weight(composite_name, component_name):
    """Get the weight for a component within a composite subject."""
    weights = COMPONENT_WEIGHTS.get(composite_name, {})
    return weights.get(component_name, 1.0)  # Default weight of 1.0
