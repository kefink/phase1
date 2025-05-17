"""
Script to generate an Excel template for student bulk uploads.
"""
import pandas as pd
import os

def create_student_upload_template():
    """Create an Excel template for student bulk uploads."""
    # Create a DataFrame with the required columns
    df = pd.DataFrame(columns=['name', 'admission_number', 'gender'])
    
    # Add some example data
    example_data = [
        ['John Doe', 'ADM001', 'Male'],
        ['Jane Smith', 'ADM002', 'Female'],
        ['Alex Johnson', 'ADM003', 'Male']
    ]
    
    for row in example_data:
        df.loc[len(df)] = row
    
    # Create the static/templates directory if it doesn't exist
    os.makedirs('new_structure/static/templates', exist_ok=True)
    
    # Save the template as Excel
    excel_path = 'new_structure/static/templates/student_upload_template.xlsx'
    df.to_excel(excel_path, index=False)
    
    # Save the template as CSV
    csv_path = 'new_structure/static/templates/student_upload_template.csv'
    df.to_csv(csv_path, index=False)
    
    print(f"Created Excel template at {excel_path}")
    print(f"Created CSV template at {csv_path}")
    
    return excel_path, csv_path

if __name__ == "__main__":
    create_student_upload_template()
