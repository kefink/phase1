"""
Performance calculation utilities for the Hillview School Management System.
"""

def get_performance_category(percentage):
    """
    Convert a percentage to a performance category.
    
    Args:
        percentage: The percentage score (0-100)
        
    Returns:
        String representing the performance category (E.E, M.E, A.E, B.E)
    """
    if percentage >= 75:
        return "E.E"  # Exceeding Expectation
    elif percentage >= 50:
        return "M.E"  # Meeting Expectation
    elif percentage >= 30:
        return "A.E"  # Approaching Expectation
    else:
        return "B.E"  # Below Expectation

def get_grade_and_points(average):
    """
    Convert an average score to a letter grade and points.
    
    Args:
        average: The average score (0-100)
        
    Returns:
        Tuple of (grade, points)
    """
    if average >= 80:
        return "A", 12
    elif average >= 75:
        return "A-", 11
    elif average >= 70:
        return "B+", 10
    elif average >= 65:
        return "B", 9
    elif average >= 60:
        return "B-", 8
    elif average >= 55:
        return "C+", 7
    elif average >= 50:
        return "C", 6
    elif average >= 45:
        return "C-", 5
    elif average >= 40:
        return "D+", 4
    elif average >= 35:
        return "D", 3
    elif average >= 30:
        return "D-", 2
    else:
        return "E", 1

def get_performance_summary(marks_data):
    """
    Generate a summary of performance categories from marks data.
    
    Args:
        marks_data: List of student mark data
        
    Returns:
        Dictionary with counts of each performance category
    """
    from collections import defaultdict
    summary = defaultdict(int)
    for student in marks_data:
        summary[student[3]] += 1
    return dict(summary)