"""
Performance calculation utilities for the Hillview School Management System.
"""

def get_performance_category(percentage):
    """
    Convert a percentage to a performance category using detailed CBC grading.

    Args:
        percentage: The percentage score (0-100)

    Returns:
        String representing the performance category (EE1, EE2, ME1, ME2, AE1, AE2, BE1, BE2)
    """
    if percentage >= 90:
        return "EE1"  # Exceeding Expectation 1
    elif percentage >= 75:
        return "EE2"  # Exceeding Expectation 2
    elif percentage >= 58:
        return "ME1"  # Meeting Expectation 1
    elif percentage >= 41:
        return "ME2"  # Meeting Expectation 2
    elif percentage >= 31:
        return "AE1"  # Approaching Expectation 1
    elif percentage >= 21:
        return "AE2"  # Approaching Expectation 2
    elif percentage >= 11:
        return "BE1"  # Below Expectation 1
    else:
        return "BE2"  # Below Expectation 2

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
    Generate CBC-compliant performance remarks based on a mark.

    Args:
        mark: The mark achieved
        total_marks: The total possible marks (default: 100)

    Returns:
        String with detailed CBC grading level (EE1, EE2, ME1, ME2, AE1, AE2, BE1, BE2)
    """
    if total_marks > 0:
        percentage = (mark / total_marks) * 100
    else:
        percentage = 0

    # Detailed CBC Grading System
    if percentage >= 90:
        return "EE1"  # Exceeding Expectation 1
    elif percentage >= 75:
        return "EE2"  # Exceeding Expectation 2
    elif percentage >= 58:
        return "ME1"  # Meeting Expectation 1
    elif percentage >= 41:
        return "ME2"  # Meeting Expectation 2
    elif percentage >= 31:
        return "AE1"  # Approaching Expectation 1
    elif percentage >= 21:
        return "AE2"  # Approaching Expectation 2
    elif percentage >= 11:
        return "BE1"  # Below Expectation 1
    else:
        return "BE2"  # Below Expectation 2

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