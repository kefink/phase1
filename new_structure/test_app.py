#!/usr/bin/env python3
"""
Simple test Flask app to demonstrate the glassmorphism UI.
"""

from flask import Flask, render_template_string

app = Flask(__name__)

# Simple HTML template with glassmorphism styles
TEACHER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Teacher Dashboard - Kirima Primary School</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <nav class="navbar">
        <a href="#" class="navbar-brand">Kirima Primary School</a>
        <ul class="navbar-nav">
            <li class="nav-item"><a href="#" class="nav-link">Dashboard</a></li>
            <li class="nav-item"><a href="#" class="logout-btn">Logout</a></li>
        </ul>
    </nav>

    <div class="container" style="max-width: 90%; margin-top: 80px;">
        <h1 class="text-center mb-4">Teacher Dashboard</h1>

        <div class="dashboard-card">
            <div class="card-header">
                <span>Upload Class Marks</span>
                <small>Complete all fields to process marks</small>
            </div>

            <form id="upload-form" class="login-form">
                <div class="form-group">
                    <label for="education_level">Education Level</label>
                    <select id="education_level" name="education_level" required>
                        <option value="">Select Education Level</option>
                        <option value="lower_primary">Lower Primary (Grades 1-3)</option>
                        <option value="upper_primary">Upper Primary (Grades 4-6)</option>
                        <option value="junior_secondary">Junior Secondary (Grades 7-9)</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="subject">Subject</label>
                    <select id="subject" name="subject" required>
                        <option value="">Select Subject</option>
                        <option value="MATHEMATICS">Mathematics</option>
                        <option value="ENGLISH">English</option>
                        <option value="KISWAHILI">Kiswahili</option>
                        <option value="SCIENCE">Science</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="term">Term</label>
                    <select id="term" name="term" required>
                        <option value="">Select Term</option>
                        <option value="Term 1">Term 1</option>
                        <option value="Term 2">Term 2</option>
                        <option value="Term 3">Term 3</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="assessment_type">Assessment Type</label>
                    <select id="assessment_type" name="assessment_type" required>
                        <option value="">Select Assessment Type</option>
                        <option value="CAT">CAT</option>
                        <option value="End Term Exam">End Term Exam</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="total_marks">Total Marks (Out Of)</label>
                    <input type="number" id="total_marks" name="total_marks" min="1" required>
                </div>

                <div class="form-group">
                    <label for="grade">Grade</label>
                    <select id="grade" name="grade" required>
                        <option value="">Select Grade</option>
                        <option value="Grade 1">Grade 1</option>
                        <option value="Grade 2">Grade 2</option>
                        <option value="Grade 3">Grade 3</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="stream">Stream</label>
                    <select id="stream" name="stream" required>
                        <option value="">Select Stream</option>
                        <option value="A">A</option>
                        <option value="B">B</option>
                    </select>
                </div>

                <div class="form-group" style="grid-column: span 2; text-align: center;">
                    <button type="submit" class="btn">
                        Upload Marks
                    </button>
                </div>
            </form>
        </div>

        <div class="dashboard-card mt-4">
            <div class="card-header">
                <span>Recent Reports</span>
                <a href="#" class="btn-outline">View All</a>
            </div>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Grade</th>
                            <th>Stream</th>
                            <th>Term</th>
                            <th>Assessment</th>
                            <th>Date</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Grade 1</td>
                            <td>A</td>
                            <td>Term 1</td>
                            <td>CAT</td>
                            <td>2025-01-15</td>
                            <td>
                                <a href="#" class="btn" style="background-color: #007BFF;">Preview</a>
                                <a href="#" class="btn" style="background-color: #28A745; margin-left: 5px;">Download</a>
                            </td>
                        </tr>
                        <tr>
                            <td>Grade 2</td>
                            <td>B</td>
                            <td>Term 1</td>
                            <td>End Term Exam</td>
                            <td>2025-01-10</td>
                            <td>
                                <a href="#" class="btn" style="background-color: #007BFF;">Preview</a>
                                <a href="#" class="btn" style="background-color: #28A745; margin-left: 5px;">Download</a>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <footer>
        <p>© 2025 Kirima Primary School - All Rights Reserved</p>
    </footer>
</body>
</html>
"""

@app.route('/')
def teacher_dashboard():
    return render_template_string(TEACHER_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
