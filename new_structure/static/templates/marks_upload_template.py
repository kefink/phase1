"""
Script to generate an Excel template for bulk marks upload.
"""
import pandas as pd
import os
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, Protection
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

def create_marks_upload_template(students, subjects, total_marks=100, grade=None, stream=None, term=None, assessment_type=None, subject_total_marks=None):
    """
    Create an Excel template for bulk marks upload.

    Args:
        students (list): List of student objects
        subjects (list): List of subject names
        total_marks (int): Maximum marks for each subject
        grade (str): Grade level
        stream (str): Stream name
        term (str): Term name
        assessment_type (str): Assessment type name

    Returns:
        str: Path to the generated Excel file
    """
    # Create a DataFrame with student names as rows and subjects as columns
    df = pd.DataFrame(index=[student.name for student in students])

    # Add admission number column
    df['Admission Number'] = [student.admission_number for student in students]

    # Add subject columns
    for subject in subjects:
        df[subject] = ''

    # Add total marks row if subject_total_marks is provided
    if subject_total_marks:
        total_marks_row = {}
        for subject in subjects:
            total_marks_row[subject] = subject_total_marks.get(subject, total_marks)
        df.loc['Total Marks'] = total_marks_row

    # Create the static/templates directory if it doesn't exist
    os.makedirs('new_structure/static/templates', exist_ok=True)

    # Define the file path
    file_name = f"marks_upload_template"
    if grade and stream:
        file_name += f"_{grade}_{stream}"
    if term:
        file_name += f"_{term}"
    if assessment_type:
        file_name += f"_{assessment_type}"

    excel_path = f'new_structure/static/templates/{file_name}.xlsx'

    # Create a workbook and add a worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Marks Entry"

    # Add header with information
    ws.merge_cells('A1:E1')
    header_cell = ws['A1']
    header_cell.value = "MARKS UPLOAD TEMPLATE"
    header_cell.font = Font(bold=True, size=14)
    header_cell.alignment = Alignment(horizontal='center')

    # Add class information
    info_row = 2
    if grade and stream:
        ws[f'A{info_row}'] = "Class:"
        ws[f'B{info_row}'] = f"{grade} {stream}"
        ws[f'A{info_row}'].font = Font(bold=True)
        info_row += 1

    if term:
        ws[f'A{info_row}'] = "Term:"
        ws[f'B{info_row}'] = term
        ws[f'A{info_row}'].font = Font(bold=True)
        info_row += 1

    if assessment_type:
        ws[f'A{info_row}'] = "Assessment:"
        ws[f'B{info_row}'] = assessment_type
        ws[f'A{info_row}'].font = Font(bold=True)
        info_row += 1

    ws[f'A{info_row}'] = "Total Marks:"
    ws[f'B{info_row}'] = total_marks
    ws[f'A{info_row}'].font = Font(bold=True)
    info_row += 1

    # Add instructions
    ws.merge_cells(f'A{info_row}:E{info_row}')
    ws[f'A{info_row}'] = "INSTRUCTIONS: Enter marks for each student in the respective subject columns. Marks should be between 0 and the total marks."
    ws[f'A{info_row}'].font = Font(italic=True)
    info_row += 2  # Add an extra blank row

    # Start of data table
    start_row = info_row

    # Add column headers
    ws[f'A{start_row}'] = "Student Name"
    ws[f'B{start_row}'] = "Admission Number"

    col_idx = 3
    for subject in subjects:
        ws[f'{get_column_letter(col_idx)}{start_row}'] = subject
        col_idx += 1

    # Style the header row
    header_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
    for col in range(1, col_idx):
        cell = ws[f'{get_column_letter(col)}{start_row}']
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    # Add student data
    row_idx = start_row + 1
    for student in students:
        ws[f'A{row_idx}'] = student.name
        ws[f'B{row_idx}'] = student.admission_number
        row_idx += 1

    # Add data validation for marks (0 to subject-specific total_marks)
    for col in range(3, col_idx):
        subject_name = ws[f'{get_column_letter(col)}{start_row}'].value
        # Get the total marks for this subject
        subject_total = total_marks
        if subject_total_marks and subject_name in subject_total_marks:
            subject_total = subject_total_marks[subject_name]

        # Add a row showing the total marks for this subject
        ws[f'{get_column_letter(col)}{row_idx}'] = f"Max: {subject_total}"
        ws[f'{get_column_letter(col)}{row_idx}'].font = Font(bold=True, color="FF0000")

        # Add data validation for each cell
        for row in range(start_row + 1, row_idx):
            cell = ws[f'{get_column_letter(col)}{row}']
            # Add data validation
            dv = DataValidation(type="whole", operator="between", formula1=0, formula2=subject_total)
            ws.add_data_validation(dv)
            dv.add(cell)

    # Auto-adjust column widths
    for col in range(1, col_idx):
        column_letter = get_column_letter(col)
        ws.column_dimensions[column_letter].width = 15

    # Make the student name column wider
    ws.column_dimensions['A'].width = 25

    # Add borders to all cells in the data table
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    for row in range(start_row, row_idx):
        for col in range(1, col_idx):
            ws[f'{get_column_letter(col)}{row}'].border = thin_border

    # Freeze the header row
    ws.freeze_panes = f'A{start_row + 1}'

    # Save the workbook
    wb.save(excel_path)

    print(f"Created Excel template at {excel_path}")

    return excel_path

def create_empty_marks_template(education_level=None):
    """
    Create an empty Excel template for marks upload with example data.

    Args:
        education_level (str): Education level (lower_primary, upper_primary, junior_secondary)

    Returns:
        str: Path to the generated Excel file
    """
    # Define example students
    example_students = [
        {'name': 'John Doe', 'admission_number': '2024001'},
        {'name': 'Jane Smith', 'admission_number': '2024002'},
        {'name': 'Michael Johnson', 'admission_number': '2024003'},
        {'name': 'Emily Brown', 'admission_number': '2024004'},
        {'name': 'David Wilson', 'admission_number': '2024005'}
    ]

    # Define example subjects based on education level
    if education_level == 'lower_primary':
        subjects = ['English', 'Kiswahili', 'Mathematics', 'Environmental Activities', 'Hygiene and Nutrition', 'Religious Education']
    elif education_level == 'upper_primary':
        subjects = ['English', 'Kiswahili', 'Mathematics', 'Science and Technology', 'Social Studies', 'Religious Education', 'Creative Arts']
    elif education_level == 'junior_secondary':
        subjects = ['English', 'Kiswahili', 'Mathematics', 'Integrated Science', 'Health Education', 'Social Studies', 'Pre-Technical Studies', 'Business Studies']
    else:
        # Default subjects if no education level specified
        subjects = ['English', 'Kiswahili', 'Mathematics', 'Science', 'Social Studies']

    # Create a DataFrame with student names as rows and subjects as columns
    df = pd.DataFrame()

    # Add student name and admission number columns
    df['Student Name'] = [student['name'] for student in example_students]
    df['Admission Number'] = [student['admission_number'] for student in example_students]

    # Add subject columns with example marks
    np.random.seed(42)  # For reproducible example marks
    for subject in subjects:
        df[subject] = np.random.randint(50, 100, size=len(example_students))

    # Create the static/templates directory if it doesn't exist
    os.makedirs('new_structure/static/templates', exist_ok=True)

    # Define the file path
    file_name = f"marks_upload_template_example"
    if education_level:
        file_name += f"_{education_level}"

    excel_path = f'new_structure/static/templates/{file_name}.xlsx'
    csv_path = f'new_structure/static/templates/{file_name}.csv'

    # Save the template as Excel
    df.to_excel(excel_path, index=False)

    # Save the template as CSV
    df.to_csv(csv_path, index=False)

    print(f"Created example Excel template at {excel_path}")
    print(f"Created example CSV template at {csv_path}")

    return excel_path, csv_path

if __name__ == "__main__":
    # Create example templates for each education level
    create_empty_marks_template('lower_primary')
    create_empty_marks_template('upper_primary')
    create_empty_marks_template('junior_secondary')
