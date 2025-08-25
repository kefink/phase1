"""
Subject Aggregation Service

This service handles the aggregation of independent subjects into composite subjects
for display purposes while maintaining independent upload functionality.
"""

from subject_config.subject_aggregation import (
    get_composite_subjects,
    get_component_subjects,
    get_composite_max_marks,
    get_component_weight
)

def aggregate_subjects_for_display(report_data):
    """
    Aggregate independent subjects into composite subjects for display.
    This version maintains component visibility for composite subjects.
    
    Args:
        report_data: The original report data with independent subjects
        
    Returns:
        Modified report data with aggregated composite subjects and component data
    """
    if not report_data or report_data.get("error"):
        return report_data
    
    # Get the original data
    class_data = report_data.get("class_data", [])
    subject_names = report_data.get("subject_names", [])
    subject_averages = report_data.get("subject_averages", {})
    
    # Create mappings for aggregation
    aggregated_subject_names = []
    aggregated_subject_averages = {}
    aggregated_class_data = []
    component_marks_data = {}  # Store component marks for display
    component_averages = {}    # Store component averages
    
    # Track which components have been processed
    processed_components = set()
    
    # First, add composite subjects
    for composite_name in get_composite_subjects():
        components = get_component_subjects(composite_name)
        
        # Check if all components exist in the current subjects
        available_components = [comp for comp in components if comp in subject_names]
        
        if available_components:  # At least one component is available
            aggregated_subject_names.append(composite_name)
            
            # Calculate composite average
            composite_total = 0
            composite_count = 0
            
            # Initialize component averages for this composite
            component_averages[composite_name] = {}
            
            for component in available_components:
                if component in subject_averages:
                    weight = get_component_weight(composite_name, component)
                    composite_total += subject_averages[component] * weight
                    composite_count += weight
                    processed_components.add(component)
                    
                    # Store component average
                    component_averages[composite_name][component] = subject_averages[component]
            
            if composite_count > 0:
                aggregated_subject_averages[composite_name] = composite_total / composite_count
            else:
                aggregated_subject_averages[composite_name] = 0
    
    # Add remaining independent subjects (not part of any composite)
    for subject_name in subject_names:
        if subject_name not in processed_components:
            aggregated_subject_names.append(subject_name)
            aggregated_subject_averages[subject_name] = subject_averages.get(subject_name, 0)
    
    # Aggregate student data with component preservation
    for student_data in class_data:
        aggregated_student = dict(student_data)  # Copy original data
        aggregated_marks = {}
        student_id = student_data.get("student_id", 0)
        
        # Initialize component marks for this student
        if student_id not in component_marks_data:
            component_marks_data[student_id] = {}
        
        # Process composite subjects
        for composite_name in get_composite_subjects():
            components = get_component_subjects(composite_name)
            available_components = [comp for comp in components if comp in subject_names]
            
            if available_components:
                composite_total = 0
                composite_max = get_composite_max_marks(composite_name)
                
                # Store component marks for display
                component_marks_data[student_id][composite_name] = {}
                
                for component in available_components:
                    component_mark = student_data.get("filtered_marks", {}).get(component, 0)
                    weight = get_component_weight(composite_name, component)
                    composite_total += component_mark * weight
                    
                    # Store individual component mark
                    component_marks_data[student_id][composite_name][component] = component_mark
                
                # Ensure the total doesn't exceed the composite max marks
                composite_total = min(composite_total, composite_max)
                aggregated_marks[composite_name] = composite_total
        
        # Add remaining independent subjects
        for subject_name in subject_names:
            if subject_name not in processed_components:
                aggregated_marks[subject_name] = student_data.get("filtered_marks", {}).get(subject_name, 0)
        
        # Update student data with aggregated marks
        aggregated_student["filtered_marks"] = aggregated_marks
        
        # Recalculate totals based on aggregated marks
        new_total = sum(aggregated_marks.values())
        aggregated_student["filtered_total"] = new_total
        
        # Recalculate average
        if len(aggregated_marks) > 0:
            aggregated_student["filtered_average"] = new_total / len(aggregated_marks)
        else:
            aggregated_student["filtered_average"] = 0
        
        aggregated_class_data.append(aggregated_student)
    
    # Re-rank students based on new totals
    aggregated_class_data.sort(key=lambda x: x["filtered_total"], reverse=True)
    for i, student in enumerate(aggregated_class_data):
        student["rank"] = i + 1
    
    # Calculate new class total and average
    if aggregated_class_data:
        class_total = sum(student["filtered_total"] for student in aggregated_class_data)
        class_average = class_total / len(aggregated_class_data) if aggregated_class_data else 0
    else:
        class_total = 0
        class_average = 0
    
    # Update the report data
    aggregated_report_data = dict(report_data)
    aggregated_report_data.update({
        "class_data": aggregated_class_data,
        "subject_names": aggregated_subject_names,
        "subject_averages": aggregated_subject_averages,
        "component_marks_data": component_marks_data,
        "component_averages": component_averages,
        "class_total": class_total,
        "class_average": class_average,
        "is_aggregated": True,  # Flag to indicate this data has been aggregated
    })
    
    return aggregated_report_data

def get_aggregated_abbreviated_subjects(subject_names):
    """
    Get abbreviated names for aggregated subjects.
    
    Args:
        subject_names: List of aggregated subject names
        
    Returns:
        List of abbreviated subject names
    """
    abbreviations = {
        "English": "ENG",
        "Kiswahili": "KIS",
        "Mathematics": "MATH",
        "Science": "SCI",
        "Social Studies": "SOC",
        "Religious Education": "RE",
        "Music": "MUS",
        "Physical Education": "PE",
        "Art": "ART",
        # Add more abbreviations as needed
    }
    
    abbreviated = []
    for subject in subject_names:
        if subject in abbreviations:
            abbreviated.append(abbreviations[subject])
        else:
            # Create abbreviation from first 3-4 characters
            abbreviated.append(subject[:4].upper())
    
    return abbreviated
