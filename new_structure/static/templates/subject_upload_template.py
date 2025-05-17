"""
Script to generate an Excel template for subject bulk uploads.
"""
import pandas as pd
import os

def create_subject_upload_template():
    """Create an Excel template for subject bulk uploads."""
    # Create a DataFrame with the required columns
    df = pd.DataFrame(columns=['name', 'education_level'])
    
    # Add some example data
    example_data = [
        ['Mathematics', 'lower_primary'],
        ['English', 'lower_primary'],
        ['Science', 'upper_primary'],
        ['Social Studies', 'upper_primary'],
        ['Physics', 'junior_secondary'],
        ['Chemistry', 'junior_secondary'],
        ['Biology', 'junior_secondary']
    ]
    
    for row in example_data:
        df.loc[len(df)] = row
    
    # Create the static/templates directory if it doesn't exist
    os.makedirs('new_structure/static/templates', exist_ok=True)
    
    # Save the template as Excel
    excel_path = 'new_structure/static/templates/subject_upload_template.xlsx'
    df.to_excel(excel_path, index=False)
    
    # Save the template as CSV
    csv_path = 'new_structure/static/templates/subject_upload_template.csv'
    df.to_csv(csv_path, index=False)
    
    print(f"Created Excel template at {excel_path}")
    print(f"Created CSV template at {csv_path}")
    
    return excel_path, csv_path

if __name__ == "__main__":
    create_subject_upload_template()
