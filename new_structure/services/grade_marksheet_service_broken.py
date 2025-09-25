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
                        stream = Stream.query.get(perm.stream_id)
                        if stream:
                            grades_dict[grade.id]['streams'].append({
                                'stream_id': stream.id,
                                'stream_name': stream.name,
                                'permission_id': perm.id
                            })
                except Exception as e:
                    print(f"Error processing permission {perm.id}: {e}")
                    continue
            
            # Get all streams for each accessible grade
            accessible_grades = []
            for grade_info in grades_dict.values():
                try:
                    # Get all streams in this grade
                    all_streams = Stream.query.filter_by(grade_id=grade_info['grade_id']).all()
                    grade_info['total_streams'] = len(all_streams)
                    
                    # Add missing streams to the list for display
                    existing_stream_ids = {s['stream_id'] for s in grade_info['streams']}
                    for stream in all_streams:
                        if stream.id not in existing_stream_ids:
                            grade_info['streams'].append({
                                'stream_id': stream.id,
                                'stream_name': stream.name,
                                'permission_id': None  # No specific permission for this stream
                            })
                    
                    # Sort streams by name
                    grade_info['streams'].sort(key=lambda x: x['stream_name'])
                    accessible_grades.append(grade_info)
                    
                except Exception as e:
                    print(f"Error getting streams for grade {grade_info['grade_id']}: {e}")
                    continue
            
            # Sort by grade name
            accessible_grades.sort(key=lambda x: x['grade_name'])
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
            Tuple (all_exist: bool, report_status: dict)
        """
        try:
            # Get all streams in this grade
            streams = Stream.query.filter_by(grade_id=grade_id).all()
            
            if not streams:
                return False, {"error": "No streams found for this grade"}
            
            report_status = {
                'grade_id': grade_id,
                'term': term,
                'assessment_type': assessment_type,
                'streams': [],
                'all_reports_exist': True
            }
            
            for stream in streams:
                # Check if marks exist for this class
                marks_exist = db.session.query(Mark).join(Student).filter(
                    Student.grade_id == grade_id,
                    Student.stream_id == stream.id,
                    Mark.term == term,
                    Mark.assessment_type == assessment_type
                ).first() is not None
                
                stream_status = {
                    'stream_id': stream.id,
                    'stream_name': stream.name,
                    'has_marks': marks_exist,
                    'student_count': Student.query.filter_by(
                        grade_id=grade_id, 
                        stream_id=stream.id
                    ).count()
                }
                
                report_status['streams'].append(stream_status)
                
                if not marks_exist:
                    report_status['all_reports_exist'] = False
            
            return report_status['all_reports_exist'], report_status
            
        except Exception as e:
            print(f"Error checking class reports: {e}")
            return False, {"error": str(e)}
    
    @staticmethod
    def can_generate_grade_marksheet(teacher_id, grade_id, term, assessment_type):
        """
        Check if a teacher can generate a grade marksheet.
        
        Requirements:
        1. Teacher must have valid permission for the grade
        2. Individual class reports must exist for all streams
        
        Args:
            teacher_id: ID of the classteacher
            grade_id: ID of the grade
            term: Term name
            assessment_type: Assessment type name
            
        Returns:
            Tuple (can_generate: bool, details: dict)
        """
        try:
            # Check if teacher has permission for this grade
            has_permission = ClassTeacherPermission.query.filter_by(
                teacher_id=teacher_id,
                grade_id=grade_id,
                is_active=True
            ).first()
            
            if not has_permission or has_permission.is_expired:
                return False, {
                    'error': 'No valid permission for this grade',
                    'reason': 'permission'
                }
            
            # Check if class reports exist
            reports_exist, report_status = GradeMarksheetService.check_class_reports_exist(
                grade_id, term, assessment_type
            )
            
            if not reports_exist:
                return False, {
                    'error': 'Individual class reports must be generated first',
                    'reason': 'missing_reports',
                    'report_status': report_status
                }
            
            return True, {
                'permission': {
                    'id': has_permission.id,
                    'expires_at': has_permission.expires_at,
                    'is_permanent': has_permission.is_permanent
                },
                'report_status': report_status
            }
            
        except Exception as e:
            print(f"Error checking grade marksheet permission: {e}")
            return False, {'error': str(e), 'reason': 'system_error'}
    
    @staticmethod
    def get_grade_marksheet_data(grade_id, term, assessment_type):
        """
        Get combined data for all streams in a grade for marksheet generation.
        
        Args:
            grade_id: ID of the grade
            term: Term name
            assessment_type: Assessment type name
            
        Returns:
            Dictionary with combined grade data
        """
        try:
            grade = Grade.query.get(grade_id)
            if not grade:
                return None
            
            # Get all students in this grade with their marks
            students_data = []
            streams = Stream.query.filter_by(grade_id=grade_id).order_by(Stream.name).all()
            
            for stream in streams:
                students = Student.query.filter_by(
                    grade_id=grade_id, 
                    stream_id=stream.id
                ).order_by(Student.first_name, Student.last_name).all()
                
                for student in students:
                    # Get marks for this student
                    marks = Mark.query.filter_by(
                        student_id=student.id,
                        term=term,
                        assessment_type=assessment_type
                    ).all()
                    
                    student_marks = {}
                    total_marks = 0
                    total_possible = 0
                    
                    for mark in marks:
                        student_marks[mark.subject_name] = {
                            'raw_score': mark.raw_score,
                            'total_marks': mark.total_marks,
                            'percentage': round((mark.raw_score / mark.total_marks) * 100, 2) if mark.total_marks > 0 else 0
                        }
                        total_marks += mark.raw_score
                        total_possible += mark.total_marks
                    
                    overall_percentage = round((total_marks / total_possible) * 100, 2) if total_possible > 0 else 0
                    
                    students_data.append({
                        'student_id': student.id,
                        'admission_number': student.admission_number,
                        'first_name': student.first_name,
                        'last_name': student.last_name,
                        'stream_name': stream.name,
                        'marks': student_marks,
                        'total_raw_marks': total_marks,
                        'total_possible_marks': total_possible,
                        'overall_percentage': overall_percentage
                    })
            
            # Calculate grade statistics
            if students_data:
                all_percentages = [s['overall_percentage'] for s in students_data]
                grade_average = round(sum(all_percentages) / len(all_percentages), 2)
                highest_score = max(all_percentages)
                lowest_score = min(all_percentages)
            else:
                grade_average = highest_score = lowest_score = 0
            
            return {
                'grade_id': grade_id,
                'grade_name': grade.name,
                'term': term,
                'assessment_type': assessment_type,
                'streams': [{'id': s.id, 'name': s.name} for s in streams],
                'students': students_data,
                'statistics': {
                    'total_students': len(students_data),
                    'grade_average': grade_average,
                    'highest_score': highest_score,
                    'lowest_score': lowest_score,
                    'total_streams': len(streams)
                },
                'generated_at': datetime.utcnow().isoformat(),
                'generated_by': session.get('teacher_id')
            }
            
        except Exception as e:
            print(f"Error getting grade marksheet data: {e}")
            return None
    
    @staticmethod
    def generate_grade_marksheet(teacher_id, grade_id, term, assessment_type, format='pdf'):
        """
        Generate a combined grade marksheet for all streams.
        
        Args:
            teacher_id: ID of the classteacher
            grade_id: ID of the grade
            term: Term name
            assessment_type: Assessment type name
            format: Output format ('pdf', 'excel', 'csv')
            
        Returns:
            Tuple (success: bool, result: dict/str)
        """
        try:
            # Check permission
            can_generate, details = GradeMarksheetService.can_generate_grade_marksheet(
                teacher_id, grade_id, term, assessment_type
            )
            
            if not can_generate:
                return False, details['error']
            
            # Get data
            marksheet_data = GradeMarksheetService.get_grade_marksheet_data(
                grade_id, term, assessment_type
            )
            
            if not marksheet_data:
                return False, "Failed to retrieve grade data"
            
            # Generate file based on format
            if format.lower() == 'pdf':
                file_path = GradeMarksheetService._generate_pdf_marksheet(marksheet_data)
            elif format.lower() == 'excel':
                file_path = GradeMarksheetService._generate_excel_marksheet(marksheet_data)
            elif format.lower() == 'csv':
                file_path = GradeMarksheetService._generate_csv_marksheet(marksheet_data)
            else:
                return False, f"Unsupported format: {format}"
            
            if file_path and os.path.exists(file_path):
                return True, {
                    'file_path': file_path,
                    'marksheet_data': marksheet_data,
                    'message': f"Grade marksheet generated successfully for {marksheet_data['grade_name']}"
                }
            else:
                return False, "Failed to generate marksheet file"
                
        except Exception as e:
            print(f"Error generating grade marksheet: {e}")
            return False, f"System error: {str(e)}"
    
    @staticmethod
    def _generate_pdf_marksheet(data):
        """Generate PDF marksheet (placeholder - implement with reportlab)."""
        # TODO: Implement PDF generation
        return None
    
    @staticmethod
    def _generate_excel_marksheet(data):
        """Generate Excel marksheet (placeholder - implement with openpyxl)."""
        # TODO: Implement Excel generation
        return None
    
    @staticmethod
    def _generate_csv_marksheet(data):
        """Generate CSV marksheet (placeholder - implement with csv module)."""
        # TODO: Implement CSV generation
        return None