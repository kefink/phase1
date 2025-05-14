"""
Utilities package for the Hillview School Management System.
This file imports and exposes utility functions for easy access.
"""
from .performance import get_performance_category, get_grade_and_points, get_performance_summary
from .pdf_generator import generate_individual_report_pdf