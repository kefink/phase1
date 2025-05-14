# Hill View School Application

A Flask-based web application for managing student records, grades, and reports for Hill View School.

## Setup Instructions

1. Clone the repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Initialize the database:
   ```
   python seed.py
   ```
4. Run the application:
   ```
   python run.py
   ```
5. Access the application at http://127.0.0.1:5000

## Login Credentials

1. **Subject Teacher**:

   - Username: `teacher1`
   - Password: `pass123`

2. **Headteacher (Admin)**:

   - Username: `headteacher`
   - Password: `admin123`

3. **Class Teacher**:
   - Username: `classteacher1`
   - Password: `class123`

## Features

- User authentication for different roles (Admin, Teacher, Class Teacher)
- Student management
- Grade and assessment tracking
- Report generation
- Performance analysis

## Technologies Used

- Flask
- SQLAlchemy
- ReportLab (for PDF generation)
- HTML/CSS/JavaScript
