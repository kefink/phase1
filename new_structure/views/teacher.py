"""
Teacher views for the Hillview School Management System.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..models import Grade, Stream, Subject, Term, AssessmentType, Student, Mark
from ..services import is_authenticated, get_role
from ..extensions import db
from ..utils import get_performance_category, get_performance_summary

# Create a blueprint for teacher routes
teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

# Decorator for requiring teacher authentication
def teacher_required(f):
    """Decorator to require teacher authentication for a route."""
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session) or get_role(session) != 'teacher':
            return redirect(url_for('auth.teacher_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@teacher_bp.route('/', methods=['GET', 'POST'])
@teacher_required
def dashboard():
    """Route for the teacher dashboard."""
    # Get data for the form
    grades = [grade.level for grade in Grade.query.all()]
    grades_dict = {grade.level: grade.id for grade in Grade.query.all()}
    subjects = [subject.name for subject in Subject.query.all()]
    terms = [term.name for term in Term.query.all()]
    assessment_types = [assessment_type.name for assessment_type in AssessmentType.query.all()]
    
    # Initialize variables
    error_message = None
    show_students = False
    students = []
    subject = ""
    grade = ""
    stream = ""
    term = ""
    assessment_type = ""
    total_marks = 0
    show_download_button = False
    
    # Fetch recent reports
    recent_reports = []
    marks = Mark.query.join(Student).join(Stream).join(Grade).join(Term).join(AssessmentType).all()
    seen_combinations = set()
    for mark in marks:
        combination = (mark.student.stream.grade.level, mark.student.stream.name, mark.term.name, mark.assessment_type.name)
        if combination not in seen_combinations:
            seen_combinations.add(combination)
            recent_reports.append({
                'grade': mark.student.stream.grade.level,
                'stream': f"Stream {mark.student.stream.name}",
                'term': mark.term.name,
                'assessment_type': mark.assessment_type.name,
                'date': mark.created_at.strftime('%Y-%m-%d') if mark.created_at else 'N/A'
            })
            if len(recent_reports) >= 5:  # Limit to 5 recent reports
                break
    
    # Handle form submission
    if request.method == "POST":
        subject = request.form.get("subject", "")
        grade = request.form.get("grade", "")
        stream = request.form.get("stream", "")
        term = request.form.get("term", "")
        assessment_type = request.form.get("assessment_type", "")
        try:
            total_marks = int(request.form.get("total_marks", 0))
        except ValueError:
            total_marks = 0
        
        # Handle upload marks request
        if "upload_marks" in request.form:
            if not all([subject, grade, stream, term, assessment_type, total_marks > 0]):
                error_message = "Please fill in all fields before uploading marks"
            else:
                stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream[-1]).first()
                if stream_obj:
                    students = [student.name for student in Student.query.filter_by(stream_id=stream_obj.id).all()]
                    show_students = True
                else:
                    error_message = f"No students found for grade {grade} stream {stream[-1]}"
        
        # Handle submit marks request
        elif "submit_marks" in request.form:
            if not all([subject, grade, stream, term, assessment_type, total_marks > 0]):
                error_message = "Please fill in all fields before submitting marks"
            else:
                stream_obj = Stream.query.join(Grade).filter(Grade.level == grade, Stream.name == stream[-1]).first()
                subject_obj = Subject.query.filter_by(name=subject).first()
                term_obj = Term.query.filter_by(name=term).first()
                assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()
                
                if not (stream_obj and subject_obj and term_obj and assessment_type_obj):
                    error_message = "Invalid selection for grade, stream, subject, term, or assessment type"
                else:
                    students = Student.query.filter_by(stream_id=stream_obj.id).all()
                    marks_data = []
                    any_marks_submitted = False
                    
                    for student in students:
                        mark_key = f"mark_{student.name.replace(' ', '_')}"
                        mark_value = request.form.get(mark_key, '')
                        if mark_value and mark_value.isdigit():
                            mark = int(mark_value)
                            if 0 <= mark <= total_marks:
                                percentage = (mark / total_marks) * 100
                                performance = get_performance_category(percentage)
                                marks_data.append([student.name, mark, round(percentage, 1), performance])
                                
                                # Save the mark to the database
                                new_mark = Mark(
                                    student_id=student.id,
                                    subject_id=subject_obj.id,
                                    term_id=term_obj.id,
                                    assessment_type_id=assessment_type_obj.id,
                                    mark=mark,
                                    total_marks=total_marks
                                )
                                db.session.add(new_mark)
                                any_marks_submitted = True
                            else:
                                error_message = f"Invalid mark for {student.name}. Must be between 0 and {total_marks}."
                                break
                        else:
                            error_message = f"Missing or invalid mark for {student.name}"
                            break
                    
                    if any_marks_submitted and not error_message:
                        db.session.commit()
                        mean_score = sum(mark[1] for mark in marks_data) / len(marks_data) if marks_data else 0
                        mean_percentage = (mean_score / total_marks) * 100 if total_marks > 0 else 0
                        mean_performance = get_performance_category(mean_percentage)
                        performance_summary = get_performance_summary(marks_data)
                        
                        return render_template(
                            "report.html",
                            data=marks_data,
                            mean_score=mean_score,
                            mean_percentage=mean_percentage,
                            mean_performance=mean_performance,
                            performance_summary=performance_summary,
                            education_level="",
                            subject=subject,
                            grade=grade,
                            stream=stream,
                            term=term,
                            assessment_type=assessment_type,
                            total_marks=total_marks
                        )
    
    # Render the teacher dashboard
    return render_template(
        "teacher.html",
        grades=grades,
        grades_dict=grades_dict,
        subjects=subjects,
        terms=terms,
        assessment_types=assessment_types,
        students=students,
        subject=subject,
        grade=grade,
        stream=stream,
        term=term,
        assessment_type=assessment_type,
        total_marks=total_marks,
        show_students=show_students,
        error_message=error_message,
        show_download_button=show_download_button,
        recent_reports=recent_reports
    )