"""
Headteacher Universal Access Service - Provides headteacher with access to all classteacher functions
across all grades and streams with intelligent class structure detection.
"""
from .class_structure_service import ClassStructureService
from ..models.academic import Grade, Stream, Subject, Term, AssessmentType, Student, Mark
from ..models.user import Teacher
from ..models.assignment import TeacherSubjectAssignment
from ..extensions import db
from sqlalchemy import func, and_
from datetime import datetime

class HeadteacherUniversalService:
    """Service providing headteacher universal access to all class functions."""
    
    @staticmethod
    def get_universal_dashboard_data():
        """
        Get comprehensive dashboard data for headteacher universal access.
        
        Returns:
            Dictionary with all necessary data for universal class management
        """
        try:
            # Get school structure
            structure = ClassStructureService.get_school_structure()
            
            # Get class statistics
            class_stats = ClassStructureService.get_class_statistics()
            
            # Get recent activity across all classes
            recent_activity = HeadteacherUniversalService._get_recent_activity()
            
            # Get performance overview
            performance_overview = HeadteacherUniversalService._get_performance_overview()
            
            # Get teacher assignments
            teacher_assignments = HeadteacherUniversalService._get_teacher_assignments()
            
            return {
                'school_structure': structure,
                'class_statistics': class_stats,
                'recent_activity': recent_activity,
                'performance_overview': performance_overview,
                'teacher_assignments': teacher_assignments,
                'available_functions': HeadteacherUniversalService._get_available_functions()
            }
            
        except Exception as e:
            print(f"Error getting universal dashboard data: {e}")
            return {}
    
    @staticmethod
    def _get_recent_activity():
        """Get recent activity across all classes."""
        try:
            # Get recent marks uploads
            # Dialect-aware 7-day window: prefer DATE_SUB(NOW(), INTERVAL 7 DAY) for MySQL, fallback to generic current_timestamp - interval
            from sqlalchemy import text
            engine_name = db.session.bind.dialect.name if db.session.bind else 'default'
            if engine_name == 'mysql':
                # MySQL compatible 7-day interval expression
                date_filter = text("DATE_SUB(NOW(), INTERVAL 7 DAY)")
            else:
                # Generic fallback: current_timestamp - 7 days (SQLite/others)
                # For SQLite, use datetime(CURRENT_TIMESTAMP, '-7 days') inline via text to avoid dialect translation issues
                if engine_name == 'sqlite':
                    date_filter = text("datetime(CURRENT_TIMESTAMP, '-7 days')")
                else:
                    # As a broad fallback, use current_timestamp (may return more results but avoids syntax errors)
                    date_filter = func.current_timestamp()  # degrade gracefully

            recent_marks = db.session.query(
                Mark.created_at,
                Grade.name.label('grade_name'),
                Stream.name.label('stream_name'),
                Subject.name.label('subject_name'),
                func.count(Mark.id).label('mark_count')
            ).join(
                Student, Mark.student_id == Student.id
            ).join(
                Stream, Student.stream_id == Stream.id
            ).join(
                Grade, Stream.grade_id == Grade.id
            ).join(
                Subject, Mark.subject_id == Subject.id
            ).filter(
                Mark.created_at >= date_filter  # date_filter is raw text or function; safe for read-only analytics
            ).group_by(
                Mark.created_at, Grade.name, Stream.name, Subject.name
            ).order_by(
                Mark.created_at.desc()
            ).limit(10).all()
            
            activity = []
            for mark in recent_marks:
                class_name = ClassStructureService.get_class_display_name(
                    mark.grade_name, mark.stream_name
                )
                activity.append({
                    'type': 'marks_upload',
                    'class_name': class_name,
                    'subject': mark.subject_name,
                    'count': mark.mark_count,
                    'date': mark.created_at.strftime('%Y-%m-%d %H:%M') if mark.created_at else '',
                    'description': f"{mark.mark_count} marks uploaded for {mark.subject_name} in {class_name}"
                })

            # Fallback: if no activity found in window, fetch last 10 uploads without date constraint
            if not activity:
                fallback_marks = db.session.query(
                    Mark.created_at,
                    Grade.name.label('grade_name'),
                    Stream.name.label('stream_name'),
                    Subject.name.label('subject_name'),
                    func.count(Mark.id).label('mark_count')
                ).join(
                    Student, Mark.student_id == Student.id
                ).join(
                    Stream, Student.stream_id == Stream.id
                ).join(
                    Grade, Stream.grade_id == Grade.id
                ).join(
                    Subject, Mark.subject_id == Subject.id
                ).group_by(
                    Mark.created_at, Grade.name, Stream.name, Subject.name
                ).order_by(
                    Mark.created_at.desc()
                ).limit(10).all()
                for mark in fallback_marks:
                    class_name = ClassStructureService.get_class_display_name(
                        mark.grade_name, mark.stream_name
                    )
                    activity.append({
                        'type': 'marks_upload',
                        'class_name': class_name,
                        'subject': mark.subject_name,
                        'count': mark.mark_count,
                        'date': mark.created_at.strftime('%Y-%m-%d %H:%M') if mark.created_at else '',
                        'description': f"{mark.mark_count} marks uploaded for {mark.subject_name} in {class_name} (all-time fallback)"
                    })
            
            return activity
            
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return []
    
    @staticmethod
    def _get_performance_overview():
        """Get performance overview across all classes."""
        try:
            # Get latest term and assessment type
            latest_term = Term.query.order_by(Term.id.desc()).first()
            latest_assessment = AssessmentType.query.filter_by(name='End Term').first()
            
            if not (latest_term and latest_assessment):
                return {}
            
            # Get performance data by class
            performance_data = db.session.query(
                Grade.name.label('grade_name'),
                Stream.name.label('stream_name'),
                func.count(Mark.id).label('total_marks'),
                func.avg(Mark.marks).label('average_marks'),
                func.count(func.distinct(Student.id)).label('student_count')
            ).join(
                Student, Mark.student_id == Student.id
            ).join(
                Stream, Student.stream_id == Stream.id
            ).join(
                Grade, Stream.grade_id == Grade.id
            ).filter(
                and_(
                    Mark.term_id == latest_term.id,
                    Mark.assessment_type_id == latest_assessment.id
                )
            ).group_by(
                Grade.name, Stream.name
            ).all()
            
            classes_performance = []
            for data in performance_data:
                class_name = ClassStructureService.get_class_display_name(
                    data.grade_name, data.stream_name
                )
                classes_performance.append({
                    'class_name': class_name,
                    'grade_name': data.grade_name,
                    'stream_name': data.stream_name,
                    'student_count': data.student_count,
                    'average_marks': round(data.average_marks, 2) if data.average_marks else 0,
                    'total_assessments': data.total_marks,
                    'performance_level': HeadteacherUniversalService._get_performance_level(data.average_marks)
                })
            
            return {
                'term': latest_term.name,
                'assessment_type': latest_assessment.name,
                'classes': classes_performance,
                'overall_average': round(
                    sum(c['average_marks'] for c in classes_performance) / len(classes_performance), 2
                ) if classes_performance else 0
            }
            
        except Exception as e:
            print(f"Error getting performance overview: {e}")
            return {}
    
    @staticmethod
    def _get_performance_level(average_marks):
        """Determine performance level based on average marks."""
        if not average_marks:
            return 'No Data'
        elif average_marks >= 80:
            return 'Excellent'
        elif average_marks >= 70:
            return 'Good'
        elif average_marks >= 60:
            return 'Satisfactory'
        elif average_marks >= 50:
            return 'Needs Improvement'
        else:
            return 'Below Average'
    
    @staticmethod
    def _get_teacher_assignments():
        """Get teacher assignments across all classes."""
        try:
            # Get class teacher assignments
            class_teachers = db.session.query(
                Teacher.id.label('id'),
                Teacher.username.label('username'),
                Teacher.first_name.label('first_name'),
                Teacher.last_name.label('last_name'),
                Grade.name.label('grade_name'),
                Stream.name.label('stream_name')
            ).join(
                Stream, Teacher.stream_id == Stream.id
            ).join(
                Grade, Stream.grade_id == Grade.id
            ).filter(
                Teacher.role == 'classteacher'
            ).all()
            
            assignments = []
            for teacher in class_teachers:
                class_name = ClassStructureService.get_class_display_name(
                    teacher.grade_name, teacher.stream_name
                )
                if teacher.first_name and teacher.last_name:
                    display_name = f"{teacher.first_name} {teacher.last_name}"
                elif teacher.first_name:
                    display_name = teacher.first_name
                elif teacher.last_name:
                    display_name = teacher.last_name
                else:
                    display_name = teacher.username

                assignments.append({
                    'teacher_id': teacher.id,
                    'teacher_name': display_name,
                    'teacher_username': teacher.username,
                    'class_name': class_name,
                    'grade_name': teacher.grade_name,
                    'stream_name': teacher.stream_name,
                    'assignment_type': 'Class Teacher'
                })
            
            return assignments
            
        except Exception as e:
            print(f"Error getting teacher assignments: {e}")
            return []
    
    @staticmethod
    def _get_available_functions():
        """Get list of available functions for headteacher universal access."""
        return [
            {
                'category': 'Student Management',
                'functions': [
                    {'name': 'View Students', 'description': 'View all students across all classes'},
                    {'name': 'Add Students', 'description': 'Add new students to any class'},
                    {'name': 'Transfer Students', 'description': 'Move students between classes'},
                    {'name': 'Student Reports', 'description': 'Generate reports for any student'}
                ]
            },
            {
                'category': 'Marks Management',
                'functions': [
                    {'name': 'Upload Marks', 'description': 'Upload marks for any class/subject'},
                    {'name': 'View Marks', 'description': 'View marks across all classes'},
                    {'name': 'Edit Marks', 'description': 'Modify marks for any student'},
                    {'name': 'Marks Analysis', 'description': 'Analyze performance across classes'}
                ]
            },
            {
                'category': 'Reports & Analytics',
                'functions': [
                    {'name': 'Class Reports', 'description': 'Generate reports for any class'},
                    {'name': 'Performance Analytics', 'description': 'Analyze performance trends'},
                    {'name': 'Comparative Analysis', 'description': 'Compare classes and streams'},
                    {'name': 'Progress Tracking', 'description': 'Track student progress over time'}
                ]
            },
            {
                'category': 'Class Administration',
                'functions': [
                    {'name': 'Class Settings', 'description': 'Configure class-specific settings'},
                    {'name': 'Subject Assignment', 'description': 'Assign subjects to classes'},
                    {'name': 'Teacher Assignment', 'description': 'Assign teachers to classes'},
                    {'name': 'Class Schedules', 'description': 'Manage class timetables'}
                ]
            }
        ]
    
    @staticmethod
    def get_class_specific_data(grade_name, stream_name=None):
        """
        Get all data for a specific class that headteacher can manage.
        
        Args:
            grade_name: Name of the grade
            stream_name: Name of the stream (optional)
            
        Returns:
            Dictionary with comprehensive class data
        """
        try:
            # Get grade and stream
            grade = Grade.query.filter_by(name=grade_name).first()
            if not grade:
                return {'error': f'Grade {grade_name} not found'}
            
            if stream_name:
                stream = Stream.query.filter_by(name=stream_name, grade_id=grade.id).first()
            else:
                stream = Stream.query.filter_by(grade_id=grade.id).first()
            
            if not stream:
                return {'error': f'Stream not found for {grade_name}'}
            
            # Get students
            students = Student.query.filter_by(stream_id=stream.id).all()
            
            # Get subjects for this grade
            subjects = Subject.query.filter_by(grade_id=grade.id).all()
            
            # Get class teacher
            class_teacher = Teacher.query.filter_by(stream_id=stream.id, role='classteacher').first()
            
            # Get recent marks
            recent_marks = Mark.query.join(Student).filter(
                Student.stream_id == stream.id
            ).order_by(Mark.created_at.desc()).limit(50).all()
            
            class_name = ClassStructureService.get_class_display_name(grade_name, stream_name)
            
            return {
                'class_name': class_name,
                'grade': {'id': grade.id, 'name': grade.name},
                'stream': {'id': stream.id, 'name': stream.name},
                'students': [
                    {
                        'id': s.id,
                        'name': s.name,
                        'admission_number': s.admission_number,
                        'gender': s.gender
                    }
                    for s in students
                ],
                'subjects': [
                    {
                        'id': s.id,
                        'name': s.name,
                        'code': s.code
                    }
                    for s in subjects
                ],
                'class_teacher': {
                    'id': class_teacher.id,
                    'name': class_teacher.full_name or class_teacher.username,
                    'username': class_teacher.username
                } if class_teacher else None,
                'student_count': len(students),
                'subject_count': len(subjects),
                'recent_activity_count': len(recent_marks)
            }
            
        except Exception as e:
            print(f"Error getting class specific data: {e}")
            return {'error': str(e)}
