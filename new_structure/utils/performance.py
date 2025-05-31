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
    Convert an average score to a performance level and points.

    Args:
        average: The average score (0-100)

    Returns:
        Tuple of (performance_level, points)
    """
    if average >= 90:
        return "EE1", 4.0
    elif average >= 75:
        return "EE2", 3.5
    elif average >= 58:
        return "ME1", 3.0
    elif average >= 41:
        return "ME2", 2.5
    elif average >= 31:
        return "AE1", 2.0
    elif average >= 21:
        return "AE2", 1.5
    elif average >= 11:
        return "BE1", 1.0
    else:
        return "BE2", 0.5

def get_performance_remarks(mark, total_marks=100):
    """
    Generate performance remarks based on a mark.

    Args:
        mark: The mark achieved
        total_marks: The total possible marks (default: 100)

    Returns:
        String with performance remarks
    """
    if total_marks > 0:
        percentage = (mark / total_marks) * 100
    else:
        percentage = 0

    if percentage >= 90:
        return "Excellent"
    elif percentage >= 80:
        return "Very Good"
    elif percentage >= 70:
        return "Good"
    elif percentage >= 60:
        return "Satisfactory"
    elif percentage >= 50:
        return "Fair"
    elif percentage >= 40:
        return "Needs Improvement"
    else:
        return "Poor"

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