"""
Admin/Headteacher views for the Hillview School Management System.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..models import Teacher, Student, Grade, Stream, Subject, Term, AssessmentType, Mark
from ..services import is_authenticated, get_role
from ..extensions import db
from functools import wraps

# Create a blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/headteacher')

# Decorator for requiring admin authentication
def admin_required(f):
    """Decorator to require admin authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session) or get_role(session) != 'headteacher':
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    """Route for the admin/headteacher dashboard."""
    # Total students
    total_students = Student.query.count()
    
    # Total teachers
    total_teachers = Teacher.query.count()
    
    # Total classes (number of streams)
    total_classes = Stream.query.count()
    
    # Average performance (compute from marks if available)
    marks = Mark.query.all()
    if marks:
        total_marks = sum(mark.mark for mark in marks if mark.mark is not None)
        count_marks = len([mark for mark in marks if mark.mark is not None])
        avg_performance = round(total_marks / count_marks, 2) if count_marks > 0 else 0
    else:
        avg_performance = 75  # Placeholder
    
    # Top performing class (stream-level performance)
    top_class = "N/A"
    top_class_score = 0
    stream_performances = {}
    for stream in Stream.query.all():
        stream_marks = Mark.query.join(Student, Mark.student_id == Student.id).filter(Student.stream_id == stream.id).all()
        if stream_marks:
            stream_avg = round(sum(mark.mark for mark in stream_marks) / len(stream_marks), 2)
            stream_name = f"{stream.grade.level} {stream.name}" if stream.grade else stream.name
            stream_performances[stream_name] = stream_avg
    if stream_performances:
        top_class = max(stream_performances, key=stream_performances.get)
        top_class_score = stream_performances[top_class]
    
    # Least performing grade
    least_performing_grade = "N/A"
    least_grade_score = 0
    grade_performances = {}
    for grade in Grade.query.all():
        grade_marks = Mark.query.join(Student, Mark.student_id == Student.id).join(Stream, Student.stream_id == Stream.id).filter(Stream.grade_id == grade.id).all()
        if grade_marks:
            grade_avg = round(sum(mark.mark for mark in grade_marks) / len(grade_marks), 2)
            grade_performances[grade.level] = grade_avg
    if grade_performances:
        least_performing_grade = min(grade_performances, key=grade_performances.get)
        least_grade_score = grade_performances[least_performing_grade]
    
    # Learners per grade with stream and gender breakdown
    learners_per_grade = {}
    gender_per_grade = {}
    streams_per_grade = {}
    
    students = Student.query.all()
    for student in students:
        grade = student.stream.grade.level if student.stream and student.stream.grade else "No Grade"
        stream_name = student.stream.name if student.stream else "No Stream"
        
        # Initialize grade-level data
        if grade not in learners_per_grade:
            learners_per_grade[grade] = 0
            gender_per_grade[grade] = {'Male': 0, 'Female': 0}
            streams_per_grade[grade] = {}
        
        # Initialize stream-level data for this grade
        if stream_name not in streams_per_grade[grade]:
            streams_per_grade[grade][stream_name] = {'total': 0, 'Male': 0, 'Female': 0}
        
        # Update counts
        learners_per_grade[grade] += 1
        streams_per_grade[grade][stream_name]['total'] += 1
        
        # Handle gender with more flexibility
        gender = student.gender.strip() if student.gender else None
        if gender:
            gender_lower = gender.lower()
            if gender_lower in ['male', 'm', 'boy']:
                gender_per_grade[grade]['Male'] += 1
                streams_per_grade[grade][stream_name]['Male'] += 1
            elif gender_lower in ['female', 'f', 'girl']:
                gender_per_grade[grade]['Female'] += 1
                streams_per_grade[grade][stream_name]['Female'] += 1
    
    # Sort grades and streams for consistent display
    learners_per_grade = dict(sorted(learners_per_grade.items()))
    gender_per_grade = dict(sorted(gender_per_grade.items()))
    streams_per_grade = {grade: dict(sorted(streams.items())) for grade, streams in sorted(streams_per_grade.items())}
    
    # Render the admin dashboard
    return render_template('headteacher.html',
                           total_students=total_students,
                           total_teachers=total_teachers,
                           avg_performance=avg_performance,
                           total_classes=total_classes,
                           top_class=top_class,
                           top_class_score=top_class_score,
                           least_performing_grade=least_performing_grade,
                           least_grade_score=least_grade_score,
                           learners_per_grade=learners_per_grade,
                           gender_per_grade=gender_per_grade,
                           streams_per_grade=streams_per_grade)

@admin_bp.route('/manage_teachers', methods=['GET', 'POST'])
@admin_required
def manage_teachers():
    """Route for managing teachers."""
    # This is a placeholder for the actual implementation
    # In a real implementation, this would handle teacher management
    return "Teacher management not implemented yet"

@admin_bp.route('/manage_subjects', methods=['GET', 'POST'])
@admin_required
def manage_subjects():
    """Route for managing subjects."""
    # This is a placeholder for the actual implementation
    # In a real implementation, this would handle subject management
    return "Subject management not implemented yet"

@admin_bp.route('/manage_grades_streams', methods=['GET', 'POST'])
@admin_required
def manage_grades_streams():
    """Route for managing grades and streams."""
    # This is a placeholder for the actual implementation
    # In a real implementation, this would handle grade and stream management
    return "Grade and stream management not implemented yet"
@admin_bp.route('/manage_terms_assessments', methods=['GET', 'POST'])
@admin_required
def manage_terms_assessments():
    """Route for managing terms and assessment types."""
    # This is a placeholder for the actual implementation
    # In a real implementation, this would handle term and assessment type management
    return render_template('manage_terms_assessments.html')