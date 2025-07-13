"""
Student Promotion Service for the Hillview School Management System.
Handles all business logic related to student promotions, including bulk promotions,
exception handling, and promotion history tracking.
"""
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sqlalchemy import and_, or_
from ..extensions import db
from ..models.academic import Student, Grade, Stream, StudentPromotionHistory, Term
from ..models.user import Teacher
from ..models.school_setup import SchoolSetup
import uuid


class DictToObject:
    """Convert dictionary to object with attribute access."""
    def __init__(self, dictionary):
        self._dict = dictionary  # Store original dict for len() support
        for key, value in dictionary.items():
            if isinstance(value, dict):
                setattr(self, key, DictToObject(value))
            elif isinstance(value, list):
                setattr(self, key, [DictToObject(item) if isinstance(item, dict) else item for item in value])
            else:
                setattr(self, key, value)

    def __len__(self):
        """Support len() function for template compatibility."""
        return len(self._dict)

    def __iter__(self):
        """Support iteration for template compatibility."""
        return iter(self._dict)

    def __contains__(self, key):
        """Support 'in' operator for template compatibility."""
        return key in self._dict

    def items(self):
        """Support .items() method for template compatibility."""
        for key, value in self._dict.items():
            if isinstance(value, dict):
                yield key, DictToObject(value)
            else:
                yield key, getattr(self, key, value)

    def keys(self):
        """Support .keys() method for template compatibility."""
        return self._dict.keys()

    def values(self):
        """Support .values() method for template compatibility."""
        for key in self._dict.keys():
            yield getattr(self, key)


class StudentPromotionService:
    """Service class for handling student promotions."""
    
    @staticmethod
    def get_promotion_preview_data(academic_year: str = None, education_level: str = None,
                                 grade_id: int = None, stream_id: int = None,
                                 page: int = 1, per_page: int = 50) -> Dict:
        """
        Get comprehensive data for promotion preview with filtering and pagination.

        Args:
            academic_year: Academic year for promotion (defaults to current)
            education_level: Filter by education level (e.g., 'Lower Primary', 'Upper Primary', 'Junior Secondary')
            grade_id: Filter by specific grade ID
            stream_id: Filter by specific stream ID
            page: Page number for pagination (starts from 1)
            per_page: Number of students per page

        Returns:
            Dictionary containing promotion preview data with pagination info
        """
        try:
            # Get current academic year if not provided
            if not academic_year:
                school_setup = SchoolSetup.query.first()
                academic_year = school_setup.current_academic_year if school_setup else "2024"
            
            # Get all active students grouped by grade
            students_by_grade = {}
            promotion_summary = {
                'total_students': 0,
                'eligible_for_promotion': 0,
                'final_grade_students': 0,
                'inactive_students': 0,
                'grades_summary': []
            }
            
            # Build query with filters - include all students (Grade 9 students will be handled for graduation)
            # Remove restrictive promotion_status filtering to show all students
            students_query = db.session.query(Student, Grade, Stream).join(
                Grade, Student.grade_id == Grade.id
            ).outerjoin(
                Stream, Student.stream_id == Stream.id
            )

            # Apply filters
            if education_level:
                students_query = students_query.filter(Grade.education_level == education_level)

            if grade_id:
                students_query = students_query.filter(Student.grade_id == grade_id)

            if stream_id:
                students_query = students_query.filter(Student.stream_id == stream_id)

            # Get total count for pagination
            total_students = students_query.count()

            # Apply pagination
            offset = (page - 1) * per_page
            students_query = students_query.order_by(
                Grade.name, Stream.name, Student.name
            ).offset(offset).limit(per_page)

            for student, grade, stream in students_query:
                grade_name = grade.name
                
                if grade_name not in students_by_grade:
                    students_by_grade[grade_name] = {
                        'grade_info': {
                            'id': grade.id,
                            'name': grade.name,
                            'education_level': grade.education_level
                        },
                        'students': [],
                        'total_count': 0,
                        'eligible_count': 0,
                        'final_grade_count': 0
                    }
                
                # Enhance student with promotion info
                student_data = student.to_dict()
                student_data['stream_name'] = stream.name if stream else 'No Stream'
                student_data['grade_name'] = grade.name
                student_data['next_grade'] = None

                # Check if this is Grade 9 (final grade)
                is_final_grade = (grade.name == '9' or grade.name == 'Grade 9' or 'grade 9' in grade.name.lower())
                student_data['is_final_grade'] = is_final_grade

                if is_final_grade:
                    student_data['promotion_action'] = 'graduate'  # Grade 9 students graduate
                    student_data['can_be_promoted'] = False
                    student_data['next_grade'] = 'Graduate'
                else:
                    student_data['promotion_action'] = 'promote'  # Default action for other grades
                    # Determine next grade and promotion eligibility
                    next_grade_name = student.get_next_grade()
                    if next_grade_name:
                        student_data['next_grade'] = next_grade_name
                        student_data['can_be_promoted'] = student.can_be_promoted()
                    else:
                        student_data['can_be_promoted'] = False
                
                students_by_grade[grade_name]['students'].append(student_data)
                students_by_grade[grade_name]['total_count'] += 1
                
                # Update summary counts
                promotion_summary['total_students'] += 1
                
                if student.is_final_grade():
                    promotion_summary['final_grade_students'] += 1
                    students_by_grade[grade_name]['final_grade_count'] += 1
                elif student.can_be_promoted():
                    promotion_summary['eligible_for_promotion'] += 1
                    students_by_grade[grade_name]['eligible_count'] += 1
            
            # Create grades summary
            for grade_name, grade_data in students_by_grade.items():
                promotion_summary['grades_summary'].append({
                    'grade_name': grade_name,
                    'total_students': grade_data['total_count'],
                    'eligible_for_promotion': grade_data['eligible_count'],
                    'final_grade_students': grade_data['final_grade_count']
                })
            
            # Calculate pagination info
            total_pages = (total_students + per_page - 1) // per_page
            has_prev = page > 1
            has_next = page < total_pages

            result_dict = {
                'success': True,
                'academic_year': academic_year,
                'students_by_grade': students_by_grade,
                'promotion_summary': promotion_summary,
                'available_streams': StudentPromotionService._get_available_streams(),
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_students,
                    'total_pages': total_pages,
                    'has_prev': has_prev,
                    'has_next': has_next,
                    'prev_num': page - 1 if has_prev else None,
                    'next_num': page + 1 if has_next else None
                },
                'filters': {
                    'education_level': education_level,
                    'grade_id': grade_id,
                    'stream_id': stream_id
                }
            }

            # Convert to object for template dot notation access
            # Convert to object for template dot notation access
            return DictToObject(result_dict)

        except Exception as e:
            error_dict = {
                'success': False,
                'error': str(e),
                'students_by_grade': {},
                'promotion_summary': {
                    'total_students': 0,
                    'eligible_for_promotion': 0,
                    'final_grade_students': 0,
                    'to_repeat': 0,
                    'to_transfer': 0
                },
                'available_streams': {},
                'pagination': {
                    'page': 1,
                    'per_page': per_page,
                    'total': 0,
                    'total_pages': 1,
                    'has_prev': False,
                    'has_next': False,
                    'prev_num': None,
                    'next_num': None
                },
                'filters': {
                    'education_level': education_level,
                    'grade_id': grade_id,
                    'stream_id': stream_id
                }
            }

            # Convert error dict to object as well
            return DictToObject(error_dict)
    
    @staticmethod
    def _get_available_streams() -> Dict[str, List[Dict]]:
        """Get available streams for each grade."""
        streams_by_grade = {}
        
        grades_with_streams = db.session.query(Grade, Stream).join(
            Stream, Grade.id == Stream.grade_id
        ).order_by(Grade.name, Stream.name).all()
        
        for grade, stream in grades_with_streams:
            if grade.name not in streams_by_grade:
                streams_by_grade[grade.name] = []
            
            streams_by_grade[grade.name].append({
                'id': stream.id,
                'name': stream.name
            })
        
        return streams_by_grade

    @staticmethod
    def get_filter_options() -> Dict:
        """Get available filter options for the promotion interface."""
        try:
            # Get education levels (include all levels including Grade 9 for graduation)
            education_levels_raw = db.session.query(Grade.education_level).distinct().all()
            education_levels = [level[0] for level in education_levels_raw if level[0]]

            # Get grades (include all grades including Grade 9) - order by name since there's no level field
            grades_raw = Grade.query.order_by(Grade.name).all()
            grades_list = [{'id': grade.id, 'name': grade.name, 'education_level': grade.education_level} for grade in grades_raw]

            # Get streams (include all streams including Grade 9) - order by grade name and stream name
            streams_raw = Stream.query.join(Grade).order_by(Grade.name, Stream.name).all()
            streams_list = [{'id': stream.id, 'name': stream.name, 'grade_name': stream.grade.name} for stream in streams_raw]

            return {
                'education_levels': education_levels,
                'grades': grades_list,
                'streams': streams_list
            }

        except Exception as e:
            return {
                'education_levels': [],
                'grades': [],
                'streams': []
            }
    
    @staticmethod
    def validate_promotion_data(promotion_data: Dict) -> Tuple[bool, str]:
        """
        Validate promotion data before processing.
        
        Args:
            promotion_data: Dictionary containing promotion instructions
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not promotion_data.get('students'):
                return False, "No students provided for promotion"
            
            if not promotion_data.get('academic_year_to'):
                return False, "Target academic year is required"
            
            # Validate each student's promotion data
            for student_data in promotion_data['students']:
                if not student_data.get('student_id'):
                    return False, "Student ID is required for all students"
                
                action = student_data.get('action', 'promote')
                if action not in ['promote', 'repeat', 'transfer', 'graduate']:
                    return False, f"Invalid promotion action: {action}"
                
                # Validate promotion targets
                if action == 'promote':
                    if not student_data.get('to_grade_id'):
                        return False, f"Target grade required for promotion of student {student_data.get('student_id')}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def process_bulk_promotion(promotion_data: Dict, promoted_by_teacher_id: int) -> Dict:
        """
        Process bulk student promotion.
        
        Args:
            promotion_data: Dictionary containing promotion instructions
            promoted_by_teacher_id: ID of teacher performing the promotion
            
        Returns:
            Dictionary containing promotion results
        """
        try:
            # Validate promotion data
            is_valid, error_message = StudentPromotionService.validate_promotion_data(promotion_data)
            if not is_valid:
                return {'success': False, 'error': error_message}
            
            # Generate batch ID for tracking
            batch_id = str(uuid.uuid4())[:8]
            promotion_results = {
                'success': True,
                'batch_id': batch_id,
                'processed_count': 0,
                'promoted_count': 0,
                'repeated_count': 0,
                'transferred_count': 0,
                'graduated_count': 0,
                'errors': []
            }
            
            # Process each student
            for student_data in promotion_data['students']:
                try:
                    result = StudentPromotionService._process_individual_promotion(
                        student_data, 
                        promotion_data['academic_year_to'],
                        promoted_by_teacher_id,
                        batch_id
                    )
                    
                    if result['success']:
                        promotion_results['processed_count'] += 1
                        promotion_results[f"{result['action']}_count"] += 1
                    else:
                        promotion_results['errors'].append({
                            'student_id': student_data['student_id'],
                            'error': result['error']
                        })
                        
                except Exception as e:
                    promotion_results['errors'].append({
                        'student_id': student_data.get('student_id', 'Unknown'),
                        'error': str(e)
                    })
            
            # Commit all changes if no critical errors
            if len(promotion_results['errors']) == 0:
                db.session.commit()
            else:
                db.session.rollback()
                promotion_results['success'] = False
            
            return promotion_results
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f"Bulk promotion failed: {str(e)}",
                'processed_count': 0
            }

    @staticmethod
    def _process_individual_promotion(student_data: Dict, academic_year_to: str,
                                    promoted_by_teacher_id: int, batch_id: str) -> Dict:
        """
        Process individual student promotion.

        Args:
            student_data: Student promotion data
            academic_year_to: Target academic year
            promoted_by_teacher_id: ID of teacher performing promotion
            batch_id: Batch ID for tracking bulk promotions

        Returns:
            Dictionary containing individual promotion result
        """
        try:
            student_id = student_data['student_id']
            action = student_data.get('action', 'promote')

            # Get student record
            student = Student.query.get(student_id)
            if not student:
                return {'success': False, 'error': f"Student {student_id} not found"}

            # Get current grade and stream
            current_grade = Grade.query.get(student.grade_id) if student.grade_id else None
            current_stream = Stream.query.get(student.stream_id) if student.stream_id else None

            if not current_grade:
                return {'success': False, 'error': f"Student {student_id} has no current grade"}

            # Create promotion history record
            promotion_history = StudentPromotionHistory(
                student_id=student_id,
                from_grade_id=student.grade_id,
                from_stream_id=student.stream_id,
                academic_year_from=student.academic_year or academic_year_to,
                promoted_by_teacher_id=promoted_by_teacher_id,
                promotion_type=action,
                promotion_reason=student_data.get('reason', 'bulk_promotion'),
                promotion_notes=student_data.get('notes', ''),
                is_bulk_promotion=True,
                bulk_promotion_batch_id=batch_id,
                final_average=student_data.get('final_average'),
                final_position=student_data.get('final_position')
            )

            # Process based on action type
            if action == 'promote':
                return StudentPromotionService._handle_promotion(
                    student, student_data, academic_year_to, promotion_history
                )
            elif action == 'repeat':
                return StudentPromotionService._handle_repetition(
                    student, student_data, academic_year_to, promotion_history
                )
            elif action == 'transfer':
                return StudentPromotionService._handle_transfer(
                    student, student_data, academic_year_to, promotion_history
                )
            elif action == 'graduate':
                return StudentPromotionService._handle_graduation(
                    student, student_data, academic_year_to, promotion_history
                )
            else:
                return {'success': False, 'error': f"Unknown action: {action}"}

        except Exception as e:
            return {'success': False, 'error': f"Individual promotion failed: {str(e)}"}

    @staticmethod
    def _handle_promotion(student: Student, student_data: Dict,
                         academic_year_to: str, promotion_history: StudentPromotionHistory) -> Dict:
        """Handle student promotion to next grade."""
        try:
            to_grade_id = student_data.get('to_grade_id')
            to_stream_id = student_data.get('to_stream_id')

            if not to_grade_id:
                return {'success': False, 'error': "Target grade ID required for promotion"}

            # Validate target grade exists
            target_grade = Grade.query.get(to_grade_id)
            if not target_grade:
                return {'success': False, 'error': f"Target grade {to_grade_id} not found"}

            # Validate target stream if provided
            if to_stream_id:
                target_stream = Stream.query.get(to_stream_id)
                if not target_stream or target_stream.grade_id != to_grade_id:
                    return {'success': False, 'error': "Invalid target stream for grade"}

            # Update promotion history
            promotion_history.to_grade_id = to_grade_id
            promotion_history.to_stream_id = to_stream_id
            promotion_history.academic_year_to = academic_year_to

            # Update student record
            student.grade_id = to_grade_id
            student.stream_id = to_stream_id
            student.academic_year = academic_year_to
            student.date_last_promoted = datetime.utcnow()
            student.promotion_status = 'active'
            student.promotion_notes = student_data.get('notes', '')

            # Save records
            db.session.add(promotion_history)
            db.session.add(student)

            return {'success': True, 'action': 'promoted'}

        except Exception as e:
            return {'success': False, 'error': f"Promotion handling failed: {str(e)}"}

    @staticmethod
    def _handle_repetition(student: Student, student_data: Dict,
                          academic_year_to: str, promotion_history: StudentPromotionHistory) -> Dict:
        """Handle student repetition of current grade."""
        try:
            # Student stays in same grade but academic year advances
            promotion_history.to_grade_id = student.grade_id
            promotion_history.to_stream_id = student.stream_id
            promotion_history.academic_year_to = academic_year_to

            # Update student record
            student.academic_year = academic_year_to
            student.promotion_status = 'active'  # Still active, just repeating
            student.promotion_notes = student_data.get('notes', 'Repeating grade')

            # Save records
            db.session.add(promotion_history)
            db.session.add(student)

            return {'success': True, 'action': 'repeated'}

        except Exception as e:
            return {'success': False, 'error': f"Repetition handling failed: {str(e)}"}

    @staticmethod
    def _handle_transfer(student: Student, student_data: Dict,
                        academic_year_to: str, promotion_history: StudentPromotionHistory) -> Dict:
        """Handle student transfer to another school."""
        try:
            # No target grade/stream for transfers
            promotion_history.academic_year_to = academic_year_to

            # Update student status
            student.promotion_status = 'transferred'
            student.academic_year = academic_year_to
            student.promotion_notes = student_data.get('notes', 'Transferred to another school')

            # Save records
            db.session.add(promotion_history)
            db.session.add(student)

            return {'success': True, 'action': 'transferred'}

        except Exception as e:
            return {'success': False, 'error': f"Transfer handling failed: {str(e)}"}

    @staticmethod
    def _handle_graduation(student: Student, student_data: Dict,
                          academic_year_to: str, promotion_history: StudentPromotionHistory) -> Dict:
        """Handle student graduation from the system."""
        try:
            # No target grade/stream for graduation
            promotion_history.academic_year_to = academic_year_to

            # Update student status
            student.promotion_status = 'graduated'
            student.academic_year = academic_year_to
            student.promotion_notes = student_data.get('notes', 'Graduated from Grade 9')

            # Save records
            db.session.add(promotion_history)
            db.session.add(student)

            return {'success': True, 'action': 'graduated'}

        except Exception as e:
            return {'success': False, 'error': f"Graduation handling failed: {str(e)}"}

    @staticmethod
    def get_promotion_history(student_id: int = None, limit: int = 50) -> List[Dict]:
        """
        Get promotion history records.

        Args:
            student_id: Optional student ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of promotion history records
        """
        try:
            query = StudentPromotionHistory.query

            if student_id:
                query = query.filter_by(student_id=student_id)

            history_records = query.order_by(
                StudentPromotionHistory.promotion_date.desc()
            ).limit(limit).all()

            return [record.to_dict() for record in history_records]

        except Exception as e:
            return []

    @staticmethod
    def get_promotion_statistics(academic_year: str = None) -> Dict:
        """
        Get promotion statistics for reporting.

        Args:
            academic_year: Academic year to analyze

        Returns:
            Dictionary containing promotion statistics
        """
        try:
            query = StudentPromotionHistory.query

            if academic_year:
                query = query.filter_by(academic_year_to=academic_year)

            # Get promotion type counts
            promotion_counts = {}
            for record in query.all():
                promotion_type = record.promotion_type
                promotion_counts[promotion_type] = promotion_counts.get(promotion_type, 0) + 1

            return {
                'success': True,
                'academic_year': academic_year,
                'promotion_counts': promotion_counts,
                'total_promotions': sum(promotion_counts.values())
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'promotion_counts': {},
                'total_promotions': 0
            }
