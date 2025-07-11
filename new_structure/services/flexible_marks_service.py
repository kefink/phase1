"""
Flexible Marks Service for managing subject-specific marks upload.
Handles filtering subjects based on teacher assignments and showing upload status.
"""
from ..models.academic import Subject, Mark, Grade, Stream, Term, AssessmentType, Student
from ..models.assignment import TeacherSubjectAssignment
from ..models.user import Teacher
from ..extensions import db
from sqlalchemy import and_, or_
from typing import Dict, List, Optional, Tuple


class FlexibleMarksService:
    """Service for managing flexible marks upload based on teacher assignments."""

    @staticmethod
    def get_teacher_assigned_subjects_for_class(teacher_id: int, grade_name: str, stream_name: str, education_level: str) -> List[Dict]:
        """
        Get subjects that a teacher is assigned to teach in a specific class.
        
        Args:
            teacher_id: ID of the teacher
            grade_name: Name of the grade (e.g., "Grade 7")
            stream_name: Name of the stream (e.g., "A")
            education_level: Education level (e.g., "junior_secondary")
            
        Returns:
            List of dictionaries containing subject info and upload status
        """
        try:
            # Get grade and stream objects
            grade_obj = Grade.query.filter_by(name=grade_name).first()
            stream_obj = Stream.query.filter_by(name=stream_name).first()
            
            if not grade_obj or not stream_obj:
                return []

            # Get teacher assignments for this specific grade/stream
            assignments = TeacherSubjectAssignment.query.filter(
                and_(
                    TeacherSubjectAssignment.teacher_id == teacher_id,
                    TeacherSubjectAssignment.grade_id == grade_obj.id,
                    or_(
                        TeacherSubjectAssignment.stream_id == stream_obj.id,
                        TeacherSubjectAssignment.stream_id == None  # Assignments for all streams
                    )
                )
            ).all()

            # Get subject IDs from assignments
            assigned_subject_ids = [assignment.subject_id for assignment in assignments]
            
            if not assigned_subject_ids:
                # If no specific assignments, return empty list
                return []

            # Get the actual subject objects
            assigned_subjects = Subject.query.filter(
                and_(
                    Subject.id.in_(assigned_subject_ids),
                    Subject.education_level == education_level
                )
            ).all()

            # Build result with upload status
            result = []
            for subject in assigned_subjects:
                subject_info = {
                    'id': subject.id,
                    'name': subject.name,
                    'education_level': subject.education_level,
                    'is_composite': subject.is_composite,
                    'assigned_by_me': True,  # This teacher is assigned to teach this subject
                    'upload_status': 'not_uploaded'
                }
                result.append(subject_info)

            return result

        except Exception as e:
            print(f"Error getting teacher assigned subjects: {str(e)}")
            return []

    @staticmethod
    def get_all_subjects_with_upload_status(teacher_id: int, grade_name: str, stream_name: str, 
                                          education_level: str, term_name: str, assessment_type_name: str) -> List[Dict]:
        """
        Get all subjects for a class with upload status information.
        Shows which subjects have been uploaded by subject teachers vs class teacher.
        
        Args:
            teacher_id: ID of the current teacher (class teacher)
            grade_name: Name of the grade
            stream_name: Name of the stream
            education_level: Education level
            term_name: Name of the term
            assessment_type_name: Name of the assessment type
            
        Returns:
            List of dictionaries containing subject info and detailed upload status
        """
        try:
            # Get grade, stream, term, and assessment type objects
            grade_obj = Grade.query.filter_by(name=grade_name).first()
            stream_obj = Stream.query.filter_by(name=stream_name).first()
            term_obj = Term.query.filter_by(name=term_name).first()
            assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type_name).first()
            
            if not all([grade_obj, stream_obj, term_obj, assessment_type_obj]):
                return []

            # Get all subjects for this education level
            all_subjects = Subject.query.filter_by(education_level=education_level).all()
            
            # Get teacher's assigned subjects
            teacher_assigned_subjects = FlexibleMarksService.get_teacher_assigned_subjects_for_class(
                teacher_id, grade_name, stream_name, education_level
            )
            teacher_assigned_ids = [s['id'] for s in teacher_assigned_subjects]

            result = []
            for subject in all_subjects:
                # Check if marks exist for this subject/class/term/assessment
                marks_exist = Mark.query.filter(
                    and_(
                        Mark.subject_id == subject.id,
                        Mark.term_id == term_obj.id,
                        Mark.assessment_type_id == assessment_type_obj.id,
                        Mark.grade_id == grade_obj.id,
                        Mark.stream_id == stream_obj.id
                    )
                ).first()

                # Determine who uploaded the marks
                uploaded_by = None
                upload_status = 'not_uploaded'
                
                if marks_exist:
                    # Find who uploaded these marks by checking teacher assignments
                    subject_teacher_assignment = TeacherSubjectAssignment.query.filter(
                        and_(
                            TeacherSubjectAssignment.subject_id == subject.id,
                            TeacherSubjectAssignment.grade_id == grade_obj.id,
                            or_(
                                TeacherSubjectAssignment.stream_id == stream_obj.id,
                                TeacherSubjectAssignment.stream_id == None
                            )
                        )
                    ).first()
                    
                    if subject_teacher_assignment:
                        uploaded_by = subject_teacher_assignment.teacher
                        if subject_teacher_assignment.teacher_id == teacher_id:
                            upload_status = 'uploaded_by_me'
                        else:
                            upload_status = 'uploaded_by_subject_teacher'
                    else:
                        upload_status = 'uploaded_by_unknown'

                subject_info = {
                    'id': subject.id,
                    'name': subject.name,
                    'education_level': subject.education_level,
                    'is_composite': subject.is_composite,
                    'assigned_to_me': subject.id in teacher_assigned_ids,
                    'upload_status': upload_status,
                    'uploaded_by': uploaded_by,
                    'can_upload': subject.id in teacher_assigned_ids,  # Can only upload assigned subjects
                    'marks_count': Mark.query.filter(
                        and_(
                            Mark.subject_id == subject.id,
                            Mark.term_id == term_obj.id,
                            Mark.assessment_type_id == assessment_type_obj.id,
                            Mark.grade_id == grade_obj.id,
                            Mark.stream_id == stream_obj.id
                        )
                    ).count()
                }
                result.append(subject_info)

            return result

        except Exception as e:
            print(f"Error getting subjects with upload status: {str(e)}")
            return []

    @staticmethod
    def get_uploadable_subjects_for_teacher(teacher_id: int, grade_name: str, stream_name: str, education_level: str) -> List[Dict]:
        """
        Get only the subjects that a teacher can upload marks for.
        This is used to filter the subject selection in the upload form.
        
        Args:
            teacher_id: ID of the teacher
            grade_name: Name of the grade
            stream_name: Name of the stream
            education_level: Education level
            
        Returns:
            List of subject dictionaries that the teacher can upload
        """
        assigned_subjects = FlexibleMarksService.get_teacher_assigned_subjects_for_class(
            teacher_id, grade_name, stream_name, education_level
        )
        
        # Filter to only include subjects the teacher can upload
        uploadable = [subject for subject in assigned_subjects if subject.get('assigned_by_me', False)]
        
        return uploadable

    @staticmethod
    def check_teacher_can_upload_subject(teacher_id: int, subject_id: int, grade_name: str, stream_name: str) -> bool:
        """
        Check if a teacher can upload marks for a specific subject in a specific class.
        
        Args:
            teacher_id: ID of the teacher
            subject_id: ID of the subject
            grade_name: Name of the grade
            stream_name: Name of the stream
            
        Returns:
            Boolean indicating if teacher can upload
        """
        try:
            grade_obj = Grade.query.filter_by(name=grade_name).first()
            stream_obj = Stream.query.filter_by(name=stream_name).first()
            
            if not grade_obj or not stream_obj:
                return False

            # Check if teacher is assigned to this subject for this grade/stream
            assignment = TeacherSubjectAssignment.query.filter(
                and_(
                    TeacherSubjectAssignment.teacher_id == teacher_id,
                    TeacherSubjectAssignment.subject_id == subject_id,
                    TeacherSubjectAssignment.grade_id == grade_obj.id,
                    or_(
                        TeacherSubjectAssignment.stream_id == stream_obj.id,
                        TeacherSubjectAssignment.stream_id == None
                    )
                )
            ).first()

            return assignment is not None

        except Exception as e:
            print(f"Error checking teacher upload permission: {str(e)}")
            return False
