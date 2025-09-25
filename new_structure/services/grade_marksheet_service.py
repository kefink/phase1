"""
Grade Marksheet Service - Handles combined grade marksheets for classteachers.

Allows classteachers to generate grade-level marksheets (all streams combined) 
for their assigned grades, but only after individual class reports exist.
"""
from flask import session
from datetime import datetime
import os
from sqlalchemy import func

class GradeMarksheetService:
    """Service for managing grade-level marksheet generation by classteachers."""
    
    @staticmethod
    def get_teacher_accessible_grades(teacher_id):
        """
        Get all grades that a classteacher can generate marksheets for.
        
        Args:
            teacher_id: ID of the classteacher
            
        Returns:
            List of grade information with stream details
        """
        # Lazy import to avoid circular imports
        from ..models import ClassTeacherPermission, Grade, Stream
        from ..extensions import db
        
        try:
            # Get active permissions for this teacher
            permissions = ClassTeacherPermission.query.filter_by(
                teacher_id=teacher_id,
                is_active=True
            ).all()
            
            # Group by grade
            grades_dict = {}
            for perm in permissions:
                if perm.is_expired:  # Skip expired permissions
                    continue
                    
                try:
                    grade = Grade.query.get(perm.grade_id)
                    if not grade:
                        continue
                        
                    if grade.id not in grades_dict:
                        grades_dict[grade.id] = {
                            'grade_id': grade.id,
                            'grade_name': grade.name,
                            'streams': [],
                            'total_streams': 0,
                            'permission_expires_at': perm.expires_at,
                            'has_valid_permission': True
                        }
                    
                    # Add stream info if specific stream permission
                    if perm.stream_id:
                        try:
                            stream = Stream.query.get(perm.stream_id)
                            if stream:
                                stream_info = {
                                    'id': stream.id,
                                    'name': stream.name,
                                    'grade_id': stream.grade_id
                                }
                                if stream_info not in grades_dict[grade.id]['streams']:
                                    grades_dict[grade.id]['streams'].append(stream_info)
                        except Exception:
                            continue
                    else:
                        # Grade-level permission - get all streams
                        try:
                            all_streams = Stream.query.filter_by(grade_id=grade.id).all()
                            for stream in all_streams:
                                stream_info = {
                                    'id': stream.id,
                                    'name': stream.name,
                                    'grade_id': stream.grade_id
                                }
                                if stream_info not in grades_dict[grade.id]['streams']:
                                    grades_dict[grade.id]['streams'].append(stream_info)
                        except Exception:
                            continue
                            
                except Exception:
                    continue
            
            # Convert to list format expected by templates
            accessible_grades = []
            for grade_info in grades_dict.values():
                # Create a simple grade object
                class SimpleGrade:
                    def __init__(self, id, name, streams):
                        self.id = id
                        self.name = name
                        self.streams = [type('Stream', (), s) for s in streams]
                
                accessible_grades.append(SimpleGrade(
                    grade_info['grade_id'],
                    grade_info['grade_name'],
                    grade_info['streams']
                ))
            
            return accessible_grades
            
        except Exception as e:
            print(f"Error getting accessible grades: {e}")
            return []
    
    @staticmethod
    def check_class_reports_exist(grade_id, term, assessment_type):
        """
        Check if individual class reports exist for all streams in a grade.
        
        Args:
            grade_id: ID of the grade
            term: Term name
            assessment_type: Assessment type name
            
        Returns:
            Tuple of (reports_exist: bool, report_status: list)
        """
        # Lazy imports
        from ..models import Stream, Student, Mark, Term, AssessmentType, Grade
        from ..extensions import db
        
        try:
            # Resolve term and assessment type to IDs for consistent filtering
            term_obj = Term.query.filter_by(name=term).first()
            assess_obj = AssessmentType.query.filter_by(name=assessment_type).first()
            term_id = term_obj.id if term_obj else None
            assess_id = assess_obj.id if assess_obj else None

            streams = Stream.query.filter_by(grade_id=grade_id).all()
            report_status = []
            all_reports_exist = True
            
            for stream in streams:
                # Check if marks exist for this stream/term/assessment
                try:
                    query = db.session.query(Mark).join(Student).filter(
                        Student.grade_id == grade_id,
                        Student.stream_id == stream.id,
                    )
                    if term_id is not None:
                        query = query.filter(Mark.term_id == term_id)
                    else:
                        # Fallback to name column if IDs unavailable in this env
                        try:
                            query = query.filter(Mark.term == term)
                        except Exception:
                            pass
                    if assess_id is not None:
                        query = query.filter(Mark.assessment_type_id == assess_id)
                    else:
                        try:
                            query = query.filter(Mark.assessment_type == assessment_type)
                        except Exception:
                            pass

                    marks_exist = query.first() is not None
                    
                    # Resolve grade name for display (avoid showing numeric IDs)
                    grade_obj = getattr(stream, 'grade', None)
                    if not grade_obj:
                        grade_obj = Grade.query.get(grade_id)
                    grade_name = grade_obj.name if grade_obj and hasattr(grade_obj, 'name') else str(grade_id)

                    report_info = {
                        'class_name': f"{grade_name} - {stream.name}",
                        'stream_id': stream.id,
                        'exists': marks_exist,
                        'student_count': Student.query.filter_by(
                            grade_id=grade_id,
                            stream_id=stream.id
                        ).count()
                    }
                    
                    report_status.append(report_info)
                    if not marks_exist:
                        all_reports_exist = False
                        
                except Exception as e:
                    print(f"Error checking marks for stream {stream.id}: {e}")
                    # On error, still show friendly class name
                    safe_grade = Grade.query.get(grade_id)
                    safe_name = safe_grade.name if safe_grade else f"Grade {grade_id}"
                    report_status.append({
                        'class_name': f"{safe_name} - {stream.name}",
                        'stream_id': stream.id,
                        'exists': False,
                        'student_count': 0
                    })
                    all_reports_exist = False
            
            return all_reports_exist, report_status
            
        except Exception as e:
            print(f"Error checking class reports: {e}")
            return False, []
    
    @staticmethod
    def can_generate_grade_marksheet(teacher_id, grade_id, term, assessment_type):
        """
        Check if a teacher can generate a grade marksheet.
        
        Args:
            teacher_id: ID of the classteacher
            grade_id: ID of the grade
            term: Term name
            assessment_type: Assessment type name
            
        Returns:
            Tuple of (can_generate: bool, details: dict)
        """
        # Lazy imports
        from ..models import ClassTeacherPermission
        
        try:
            # Check permission
            has_permission = ClassTeacherPermission.query.filter_by(
                teacher_id=teacher_id,
                grade_id=grade_id,
                is_active=True
            ).first()
            
            if not has_permission or has_permission.is_expired:
                return False, {
                    'error': 'No permission to generate marksheets for this grade',
                    'reason': 'permission_denied'
                }
            
            # Check if class reports exist
            reports_exist, report_status = GradeMarksheetService.check_class_reports_exist(
                grade_id, term, assessment_type
            )
            
            if not reports_exist:
                missing_reports = [r['class_name'] for r in report_status if not r['exists']]
                return False, {
                    'error': f'Individual class reports must be generated first',
                    'reason': 'missing_prerequisites',
                    'missing_reports': missing_reports,
                    'report_status': report_status
                }
            
            return True, {
                'message': 'Grade marksheet can be generated',
                'report_status': report_status
            }
            
        except Exception as e:
            print(f"Error checking grade marksheet eligibility: {e}")
            return False, {
                'error': f'System error: {str(e)}',
                'reason': 'system_error'
            }
    
    @staticmethod
    def get_grade_marksheet_data(grade_id, term, assessment_type):
        """
        Get combined data for a grade marksheet.
        
        Args:
            grade_id: ID of the grade
            term: Term name
            assessment_type: Assessment type name
            
        Returns:
            Dict with marksheet data or None if error
        """
        # Lazy imports
        from ..models import Grade, Stream, Student, Mark, Term, AssessmentType
        from ..extensions import db
        
        try:
            grade = Grade.query.get(grade_id)
            if not grade:
                return None
                
            # Get all streams for this grade
            streams = Stream.query.filter_by(grade_id=grade_id).order_by(Stream.name).all()
            all_students = []

            # Resolve term and assessment type IDs (prefer IDs; fallback to names)
            term_obj = Term.query.filter_by(name=term).first()
            assess_obj = AssessmentType.query.filter_by(name=assessment_type).first()
            term_id = term_obj.id if term_obj else None
            assess_id = assess_obj.id if assess_obj else None
            
            for stream in streams:
                students = Student.query.filter_by(
                    grade_id=grade_id,
                    stream_id=stream.id
                ).order_by(Student.first_name, Student.last_name).all()
                
                for student in students:
                    marks_q = Mark.query.filter_by(student_id=student.id)
                    if term_id is not None:
                        marks_q = marks_q.filter(Mark.term_id == term_id)
                    else:
                        try:
                            marks_q = marks_q.filter(Mark.term == term)
                        except Exception:
                            pass
                    if assess_id is not None:
                        marks_q = marks_q.filter(Mark.assessment_type_id == assess_id)
                    else:
                        try:
                            marks_q = marks_q.filter(Mark.assessment_type == assessment_type)
                        except Exception:
                            pass
                    marks = marks_q.all()
                    
                    # Create student data with marks
                    student_data = {
                        'id': student.id,
                        'name': f"{student.first_name} {student.last_name}",
                        'class_name': f"Grade {grade.name}",
                        'stream': stream.name,
                        'grades': {},
                        'total': 0,
                        'average': 0
                    }
                    
                    # Add marks by subject
                    total_marks = 0
                    subject_count = 0
                    for mark in marks:
                        if mark.subject and mark.marks is not None:
                            student_data['grades'][mark.subject.name] = mark.marks
                            total_marks += mark.marks
                            subject_count += 1
                    
                    if subject_count > 0:
                        student_data['total'] = total_marks
                        student_data['average'] = round(total_marks / subject_count, 1)
                    
                    all_students.append(student_data)
            
            # Get all subjects
            subjects = set()
            for student in all_students:
                subjects.update(student['grades'].keys())
            subjects = sorted(list(subjects))
            
            return {
                'grade_id': grade_id,
                'grade_name': grade.name,
                'term': term,
                'assessment_type': assessment_type,
                'streams': [{'id': s.id, 'name': s.name} for s in streams],
                'total_students': len(all_students),
                'subjects': subjects,
                'students': all_students
            }
            
        except Exception as e:
            print(f"Error getting grade marksheet data: {e}")
            return None
    
    @staticmethod
    def generate_grade_marksheet(teacher_id, grade_id, term, assessment_type, format_type='pdf'):
        """
        Generate a downloadable grade marksheet file.
        
        Args:
            teacher_id: ID of the classteacher
            grade_id: ID of the grade
            term: Term name
            assessment_type: Assessment type name
            format_type: File format ('pdf' or 'excel')
            
        Returns:
            Tuple of (success: bool, result: dict or str)
        """
        try:
            # Check permission first
            can_generate, details = GradeMarksheetService.can_generate_grade_marksheet(
                teacher_id, grade_id, term, assessment_type
            )
            
            if not can_generate:
                return False, details.get('error', 'Cannot generate marksheet')
            
            # Get marksheet data
            marksheet_data = GradeMarksheetService.get_grade_marksheet_data(
                grade_id, term, assessment_type
            )
            
            if not marksheet_data:
                return False, "Failed to retrieve grade data"
            
            # For now, return success with mock file path
            # In a real implementation, this would generate actual PDF/Excel files
            return True, {
                'file_path': '/tmp/mock_marksheet.pdf',
                'marksheet_data': marksheet_data
            }
            
        except Exception as e:
            print(f"Error generating grade marksheet: {e}")
            return False, f"System error: {str(e)}"