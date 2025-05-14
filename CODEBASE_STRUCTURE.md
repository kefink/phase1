# Hill View School Application - Codebase Structure

## Overview

The Hill View School Application is a Flask-based web application designed to manage student records, grades, and reports for a school. The application supports different user roles (headteacher/admin, teacher, and class teacher) with specific functionalities for each role.

## Project Structure

```
hillview_mvp/
├── app.py                  # Main Flask application file with routes and logic
├── models.py               # Database models using SQLAlchemy ORM
├── database.py             # Basic database initialization (legacy)
├── seed.py                 # Script to seed the database with initial data
├── run.py                  # Script to run the application
├── kirima_primary.db       # SQLite database file
├── static/                 # Static files (CSS, JS, images)
│   ├── css/
│   │   ├── headteacher.css
│   │   └── style.css
│   ├── js/
│   │   ├── classteacher.js
│   │   └── script.js
│   └── hv.jpg
└── templates/              # HTML templates
    ├── admin_login.html
    ├── class_report.html
    ├── classteacher.html
    ├── classteacher_login.html
    ├── confirm_grade_marksheet.html
    ├── headteacher.html
    ├── login.html
    ├── manage_grades_streams.html
    ├── manage_students.html
    ├── manage_subjects.html
    ├── manage_teachers.html
    ├── manage_terms_assessments.html
    ├── preview_class_report.html
    ├── preview_grade_marksheet.html
    ├── preview_individual_report.html
    ├── report.html
    ├── teacher.html
    └── teacher_login.html
```

## Database Models

The application uses SQLAlchemy ORM to define and interact with the database. The main models are:

1. **Subject**: Represents a subject taught in the school
   - Fields: id, name, education_level
   - Relationships: marks, teachers

2. **Teacher**: Represents a teacher in the school
   - Fields: id, username, password, role
   - Relationships: stream, subjects

3. **Grade**: Represents a grade level (e.g., Grade 1, Grade 2)
   - Fields: id, level
   - Relationships: streams

4. **Stream**: Represents a class stream (e.g., A, B, C)
   - Fields: id, name, grade_id
   - Relationships: students, teachers

5. **Term**: Represents a school term (e.g., Term 1, Term 2)
   - Fields: id, name
   - Relationships: marks

6. **AssessmentType**: Represents a type of assessment (e.g., midterm, endterm)
   - Fields: id, name
   - Relationships: marks

7. **Student**: Represents a student in the school
   - Fields: id, name, admission_number, stream_id, gender
   - Relationships: marks, stream

8. **Mark**: Represents a student's mark in a subject
   - Fields: id, student_id, subject_id, term_id, assessment_type_id, mark, total_marks, created_at
   - Relationships: student, subject, term, assessment_type

## Authentication and User Roles

The application supports three user roles:

1. **Headteacher/Admin**: Can manage teachers, subjects, grades, streams, terms, and assessment types
   - Username: `headteacher`
   - Password: `admin123`

2. **Teacher**: Can enter marks for specific subjects and generate reports
   - Username: `teacher1`
   - Password: `pass123`

3. **Class Teacher**: Can manage students in their assigned class and generate class reports
   - Username: `classteacher1`
   - Password: `class123`

## Main Routes and Functionality

1. **Authentication Routes**:
   - `/`: Main login page
   - `/admin_login`: Headteacher login
   - `/teacher_login`: Teacher login
   - `/classteacher_login`: Class teacher login

2. **Dashboard Routes**:
   - `/headteacher`: Headteacher dashboard
   - `/teacher`: Teacher dashboard
   - `/classteacher`: Class teacher dashboard

3. **Management Routes**:
   - `/manage_teachers`: Manage teachers (add, view, delete)
   - `/manage_subjects`: Manage subjects (add, view, delete)
   - `/manage_grades_streams`: Manage grades and streams (add, view, delete)
   - `/manage_terms_assessments`: Manage terms and assessment types (add, view, delete)
   - `/manage_students`: Manage students (add, view, delete, bulk upload)

4. **Report Routes**:
   - `/preview_class_report`: Preview class report
   - `/download_class_report`: Download class report as PDF
   - `/preview_individual_report`: Preview individual student report
   - `/download_individual_report`: Download individual student report as PDF
   - `/preview_grade_marksheet`: Preview grade marksheet
   - `/download_grade_marksheet`: Download grade marksheet as PDF

## Key Features

1. **User Authentication**: Secure login for different user roles
2. **Student Management**: Add, view, edit, and delete students
3. **Mark Entry**: Enter and manage student marks for different subjects
4. **Report Generation**: Generate and download various reports (class, individual, marksheet)
5. **Performance Analysis**: Calculate and display performance statistics
6. **CSRF Protection**: All forms are protected against CSRF attacks

## Technologies Used

1. **Backend**: Flask (Python web framework)
2. **Database**: SQLite with SQLAlchemy ORM
3. **Frontend**: HTML, CSS, JavaScript
4. **PDF Generation**: ReportLab
5. **Data Processing**: Pandas

## Running the Application

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Initialize the database:
   ```
   python seed.py
   ```

3. Run the application:
   ```
   python run.py
   ```

4. Access the application at http://127.0.0.1:5000
