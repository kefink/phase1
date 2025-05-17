"""
Excel export services for the Hillview School Management System.
"""
import pandas as pd
import os
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def generate_grade_marksheet_excel(grade, term, assessment_type, subjects, data, statistics):
    """
    Generate an Excel file for a grade marksheet.
    
    Args:
        grade (str): Grade level
        term (str): Term name
        assessment_type (str): Assessment type name
        subjects (list): List of subject objects
        data (list): List of student data dictionaries
        statistics (dict): Dictionary of statistics
        
    Returns:
        BytesIO: Excel file as a BytesIO object
    """
    # Create a BytesIO object to store the Excel file
    output = BytesIO()
    
    # Create a Pandas Excel writer using the BytesIO object
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Create the main marksheet
        create_marksheet_sheet(writer, grade, term, assessment_type, subjects, data)
        
        # Create the statistics sheet
        create_statistics_sheet(writer, grade, term, assessment_type, subjects, statistics)
        
        # Create the charts sheet
        create_charts_sheet(writer, grade, term, assessment_type, statistics)
        
        # Create a sheet for each stream
        for stream_name, stream_data in statistics['stream_data'].items():
            create_stream_sheet(writer, grade, stream_name, term, assessment_type, subjects, 
                               [d for d in data if d['stream'] == stream_name], stream_data)
    
    # Seek to the beginning of the BytesIO object
    output.seek(0)
    
    return output

def create_marksheet_sheet(writer, grade, term, assessment_type, subjects, data):
    """Create the main marksheet sheet in the Excel file."""
    # Extract subject names
    subject_names = [subject.name for subject in subjects]
    
    # Create a DataFrame for the marksheet
    df_data = []
    for student in data:
        row = {
            'Rank': student['rank'],
            'Name': student['name'],
            'Stream': student['stream'],
            'Admission Number': student.get('admission_number', ''),
            'Gender': student.get('gender', '').capitalize()
        }
        
        # Add subject marks
        for subject_name in subject_names:
            row[subject_name] = student['marks'].get(subject_name, '-')
        
        # Add totals and averages
        row['Total'] = student['total']
        row['Average (%)'] = student['percentage']
        row['Grade'] = student['grade']
        
        df_data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(df_data)
    
    # Write the DataFrame to the Excel file
    df.to_excel(writer, sheet_name='Grade Marksheet', index=False)
    
    # Get the xlsxwriter workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['Grade Marksheet']
    
    # Add a header with the grade, term, and assessment type
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#D9E1F2'
    })
    
    # Merge cells for the header
    worksheet.merge_range('A1:E1', f"{grade} - {term} - {assessment_type}", header_format)
    
    # Add the date
    date_format = workbook.add_format({
        'italic': True,
        'align': 'right'
    })
    worksheet.write('F1', f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", date_format)
    
    # Format the column headers
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#D7E4BC',
        'border': 1
    })
    
    # Apply the header format to all column headers
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(1, col_num, value, header_format)
    
    # Set column widths
    worksheet.set_column('A:A', 5)  # Rank
    worksheet.set_column('B:B', 25)  # Name
    worksheet.set_column('C:C', 8)   # Stream
    worksheet.set_column('D:D', 15)  # Admission Number
    worksheet.set_column('E:E', 8)   # Gender
    
    # Set subject column widths
    for i in range(len(subject_names)):
        worksheet.set_column(5 + i, 5 + i, 10)
    
    # Set total and average column widths
    worksheet.set_column(5 + len(subject_names), 5 + len(subject_names), 10)  # Total
    worksheet.set_column(6 + len(subject_names), 6 + len(subject_names), 12)  # Average
    worksheet.set_column(7 + len(subject_names), 7 + len(subject_names), 10)  # Grade
    
    # Add conditional formatting for the grades
    grade_col = 7 + len(subject_names)
    worksheet.conditional_format(2, grade_col, 1 + len(data), grade_col, {
        'type': 'text',
        'criteria': 'containing',
        'value': 'Excellent',
        'format': workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
    })
    worksheet.conditional_format(2, grade_col, 1 + len(data), grade_col, {
        'type': 'text',
        'criteria': 'containing',
        'value': 'Very Good',
        'format': workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C5700'})
    })
    worksheet.conditional_format(2, grade_col, 1 + len(data), grade_col, {
        'type': 'text',
        'criteria': 'containing',
        'value': 'Good',
        'format': workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C5700'})
    })
    worksheet.conditional_format(2, grade_col, 1 + len(data), grade_col, {
        'type': 'text',
        'criteria': 'containing',
        'value': 'Average',
        'format': workbook.add_format({'bg_color': '#FFCC99', 'font_color': '#974706'})
    })
    worksheet.conditional_format(2, grade_col, 1 + len(data), grade_col, {
        'type': 'text',
        'criteria': 'containing',
        'value': 'Below Average',
        'format': workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
    })
    worksheet.conditional_format(2, grade_col, 1 + len(data), grade_col, {
        'type': 'text',
        'criteria': 'containing',
        'value': 'Poor',
        'format': workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
    })

def create_statistics_sheet(writer, grade, term, assessment_type, subjects, statistics):
    """Create a statistics sheet in the Excel file."""
    # Get the workbook and create a new worksheet
    workbook = writer.book
    worksheet = workbook.add_worksheet('Statistics')
    
    # Add a header with the grade, term, and assessment type
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#D9E1F2'
    })
    
    # Merge cells for the header
    worksheet.merge_range('A1:D1', f"{grade} - {term} - {assessment_type} - Statistics", header_format)
    
    # Add the date
    date_format = workbook.add_format({
        'italic': True,
        'align': 'right'
    })
    worksheet.write('E1', f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", date_format)
    
    # Add section headers
    section_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'bg_color': '#D7E4BC',
        'border': 1
    })
    
    # Overall Statistics
    row = 3
    worksheet.merge_range(f'A{row}:D{row}', 'Overall Statistics', section_format)
    row += 1
    
    # Add overall statistics
    worksheet.write(f'A{row}', 'Total Students:')
    worksheet.write(f'B{row}', statistics['total_students'])
    row += 1
    
    worksheet.write(f'A{row}', 'Overall Average:')
    worksheet.write(f'B{row}', f"{statistics['overall_average']}%")
    row += 2
    
    # Stream Statistics
    worksheet.merge_range(f'A{row}:D{row}', 'Stream Statistics', section_format)
    row += 1
    
    # Add headers for stream statistics
    worksheet.write(f'A{row}', 'Stream')
    worksheet.write(f'B{row}', 'Students')
    worksheet.write(f'C{row}', 'Average (%)')
    row += 1
    
    # Add stream statistics
    for stream_name, stream_data in statistics['stream_data'].items():
        worksheet.write(f'A{row}', stream_name)
        worksheet.write(f'B{row}', stream_data['count'])
        worksheet.write(f'C{row}', stream_data['average'])
        row += 1
    
    row += 1
    
    # Subject Statistics
    worksheet.merge_range(f'A{row}:D{row}', 'Subject Statistics', section_format)
    row += 1
    
    # Add headers for subject statistics
    worksheet.write(f'A{row}', 'Subject')
    worksheet.write(f'B{row}', 'Average (%)')
    row += 1
    
    # Add subject statistics
    for subject_name, average in statistics['subject_averages'].items():
        worksheet.write(f'A{row}', subject_name)
        worksheet.write(f'B{row}', average)
        row += 1
    
    row += 1
    
    # Performance Statistics
    worksheet.merge_range(f'A{row}:D{row}', 'Performance Statistics', section_format)
    row += 1
    
    # Add headers for performance statistics
    worksheet.write(f'A{row}', 'Grade')
    worksheet.write(f'B{row}', 'Count')
    worksheet.write(f'C{row}', 'Percentage')
    row += 1
    
    # Add performance statistics
    for grade_label, count in statistics['performance_counts'].items():
        worksheet.write(f'A{row}', grade_label)
        worksheet.write(f'B{row}', count)
        worksheet.write(f'C{row}', f"{(count / statistics['total_students']) * 100:.1f}%" if statistics['total_students'] > 0 else "0%")
        row += 1
    
    row += 1
    
    # Gender Statistics
    worksheet.merge_range(f'A{row}:D{row}', 'Gender Statistics', section_format)
    row += 1
    
    # Add headers for gender statistics
    worksheet.write(f'A{row}', 'Gender')
    worksheet.write(f'B{row}', 'Count')
    worksheet.write(f'C{row}', 'Percentage')
    row += 1
    
    # Add gender statistics
    for gender, count in statistics['gender_counts'].items():
        worksheet.write(f'A{row}', gender.capitalize())
        worksheet.write(f'B{row}', count)
        worksheet.write(f'C{row}', f"{(count / statistics['total_students']) * 100:.1f}%" if statistics['total_students'] > 0 else "0%")
        row += 1

def create_charts_sheet(writer, grade, term, assessment_type, statistics):
    """Create a charts sheet in the Excel file."""
    # This is a placeholder for chart generation
    # In a real implementation, you would create charts using matplotlib or xlsxwriter
    pass

def create_stream_sheet(writer, grade, stream, term, assessment_type, subjects, data, stream_data):
    """Create a sheet for a specific stream in the Excel file."""
    # Extract subject names
    subject_names = [subject.name for subject in subjects]
    
    # Create a DataFrame for the stream marksheet
    df_data = []
    for student in data:
        row = {
            'Rank': student['rank'],
            'Name': student['name'].split(' (')[0],  # Remove the stream name from the student name
            'Admission Number': student.get('admission_number', ''),
            'Gender': student.get('gender', '').capitalize()
        }
        
        # Add subject marks
        for subject_name in subject_names:
            row[subject_name] = student['marks'].get(subject_name, '-')
        
        # Add totals and averages
        row['Total'] = student['total']
        row['Average (%)'] = student['percentage']
        row['Grade'] = student['grade']
        
        df_data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(df_data)
    
    # Write the DataFrame to the Excel file
    sheet_name = f"Stream {stream}"
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Get the xlsxwriter workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    # Add a header with the grade, stream, term, and assessment type
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#D9E1F2'
    })
    
    # Merge cells for the header
    worksheet.merge_range('A1:D1', f"{grade} Stream {stream} - {term} - {assessment_type}", header_format)
    
    # Add the date
    date_format = workbook.add_format({
        'italic': True,
        'align': 'right'
    })
    worksheet.write('E1', f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", date_format)
    
    # Format the column headers
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#D7E4BC',
        'border': 1
    })
    
    # Apply the header format to all column headers
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(1, col_num, value, header_format)
    
    # Set column widths
    worksheet.set_column('A:A', 5)  # Rank
    worksheet.set_column('B:B', 25)  # Name
    worksheet.set_column('C:C', 15)  # Admission Number
    worksheet.set_column('D:D', 8)   # Gender
    
    # Set subject column widths
    for i in range(len(subject_names)):
        worksheet.set_column(4 + i, 4 + i, 10)
    
    # Set total and average column widths
    worksheet.set_column(4 + len(subject_names), 4 + len(subject_names), 10)  # Total
    worksheet.set_column(5 + len(subject_names), 5 + len(subject_names), 12)  # Average
    worksheet.set_column(6 + len(subject_names), 6 + len(subject_names), 10)  # Grade
