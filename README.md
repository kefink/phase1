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

**Database has been cleaned of all test data!**

**Current Admin Account:**

- Username: `headteacher`
- Password: `admin123`

**To add your own data:**

1. Login as headteacher
2. Use the admin interface to create your own:
   - Grades and streams
   - Subjects
   - Terms and assessments
   - Teachers
   - Students
3. Login as classteacher to upload marks
4. View analytics with your real data

See `FRESH_DATA_SETUP_GUIDE.md` for detailed instructions.

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
