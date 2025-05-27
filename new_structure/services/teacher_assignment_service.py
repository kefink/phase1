"""
Teacher Assignment Service for managing subject-teacher relationships.
"""
from ..models import TeacherSubjectAssignment, Subject, Grade, Stream
from ..extensions import db

def get_teacher_assigned_subjects(teacher_id, grade_id=None, stream_id=None):
    """
    Get subjects assigned to a specific teacher.
    
    Args:
        teacher_id: ID of the teacher
        grade_id: Optional grade filter
        stream_id: Optional stream filter
        
    Returns:
        List of Subject objects assigned to the teacher
    """
    query = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id)
    
    if grade_id:
        query = query.filter_by(grade_id=grade_id)
    if stream_id:
        query = query.filter_by(stream_id=stream_id)
    
    assignments = query.all()
    subject_ids = [assignment.subject_id for assignment in assignments]
    
    if not subject_ids:
        return []
    
    return Subject.query.filter(Subject.id.in_(subject_ids)).all()

def get_teacher_assigned_grades_streams(teacher_id):
    """
    Get grades and streams assigned to a specific teacher.
    
    Args:
        teacher_id: ID of the teacher
        
    Returns:
        Dict with 'grades' and 'streams' lists
    """
    assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id).all()
    
    grade_ids = list(set([assignment.grade_id for assignment in assignments]))
    stream_ids = list(set([assignment.stream_id for assignment in assignments if assignment.stream_id]))
    
    grades = Grade.query.filter(Grade.id.in_(grade_ids)).all() if grade_ids else []
    streams = Stream.query.filter(Stream.id.in_(stream_ids)).all() if stream_ids else []
    
    return {
        'grades': grades,
        'streams': streams,
        'grade_ids': grade_ids,
        'stream_ids': stream_ids
    }

def is_teacher_assigned_to_subject(teacher_id, subject_id, grade_id, stream_id=None):
    """
    Check if a teacher is assigned to teach a specific subject.
    
    Args:
        teacher_id: ID of the teacher
        subject_id: ID of the subject
        grade_id: ID of the grade
        stream_id: Optional ID of the stream
        
    Returns:
        Boolean indicating if teacher is assigned
    """
    query = TeacherSubjectAssignment.query.filter_by(
        teacher_id=teacher_id,
        subject_id=subject_id,
        grade_id=grade_id
    )
    
    if stream_id:
        query = query.filter_by(stream_id=stream_id)
    
    return query.first() is not None

def get_teacher_recent_reports(teacher_id, limit=5):
    """
    Get recent reports for subjects assigned to a teacher.
    
    Args:
        teacher_id: ID of the teacher
        limit: Maximum number of reports to return
        
    Returns:
        List of recent report data
    """
    from ..models import Mark, Student, Term, AssessmentType
    from sqlalchemy import func
    
    # Get teacher's assigned subjects
    assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id).all()
    subject_ids = [assignment.subject_id for assignment in assignments]
    
    if not subject_ids:
        return []
    
    # Get recent marks for assigned subjects
    marks = Mark.query.filter(
        Mark.subject_id.in_(subject_ids)
    ).join(Student).join(Stream).join(Grade).join(Term).join(AssessmentType).order_by(
        Mark.created_at.desc()
    ).limit(limit * 3).all()  # Get more to filter unique combinations
    
    seen_combinations = set()
    recent_reports = []
    
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
            if len(recent_reports) >= limit:
                break
    
    return recent_reports
