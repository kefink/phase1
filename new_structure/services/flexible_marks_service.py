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
    def get_teacher_all_class_assignments(teacher_id: int) -> List[Dict]:
        """
        Get all classes where a teacher has subject assignments.
        This includes both their assigned class (if they're a class teacher) and other classes where they teach subjects.

        Args:
            teacher_id: ID of the teacher

        Returns:
            List of dictionaries containing class info and subjects taught
        """
        try:
            # Get all assignments for this teacher
            assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id).all()

            if not assignments:
                return []

            # Group assignments by grade/stream
            class_assignments = {}

            for assignment in assignments:
                grade_obj = Grade.query.get(assignment.grade_id)
                stream_obj = Stream.query.get(assignment.stream_id) if assignment.stream_id else None
                subject_obj = Subject.query.get(assignment.subject_id)

                if not grade_obj or not subject_obj:
                    continue

                # Create class key
                stream_name = stream_obj.name if stream_obj else "All"
                class_key = f"{grade_obj.name}_{stream_name}"

                if class_key not in class_assignments:
                    class_assignments[class_key] = {
                        'grade_name': grade_obj.name,
                        'stream_name': stream_name,
                        'education_level': grade_obj.education_level,
                        'is_class_teacher': assignment.is_class_teacher,
                        'subjects': [],
                        'grade_id': grade_obj.id,
                        'stream_id': stream_obj.id if stream_obj else None
                    }

                # Add subject to this class
                class_assignments[class_key]['subjects'].append({
                    'id': subject_obj.id,
                    'name': subject_obj.name,
                    'is_composite': subject_obj.is_composite,
                    'is_class_teacher_assignment': assignment.is_class_teacher
                })

                # Update class teacher status if any assignment is class teacher
                if assignment.is_class_teacher:
                    class_assignments[class_key]['is_class_teacher'] = True

            return list(class_assignments.values())

        except Exception as e:
            print(f"Error getting teacher class assignments: {str(e)}")
            return []

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

    @staticmethod
    def can_teacher_access_classteacher_portal(teacher_id: int) -> bool:
        """
        Check if a teacher can access the class teacher portal.
        This includes both actual class teachers and subject teachers who teach in any class.

        Args:
            teacher_id: ID of the teacher

        Returns:
            Boolean indicating if teacher can access the portal
        """
        try:
            # Check if teacher has any subject assignments
            assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id).first()
            return assignments is not None

        except Exception as e:
            print(f"Error checking class teacher portal access: {str(e)}")
            return False

    @staticmethod
    def get_teacher_portal_summary(teacher_id: int) -> Dict:
        """
        Get a summary of teacher's access and assignments for portal display.

        Args:
            teacher_id: ID of the teacher

        Returns:
            Dictionary with teacher's portal access summary
        """
        try:
            teacher = Teacher.query.get(teacher_id)
            if not teacher:
                return {'error': 'Teacher not found'}

            # Get all class assignments
            class_assignments = FlexibleMarksService.get_teacher_all_class_assignments(teacher_id)

            # Determine teacher type
            is_actual_class_teacher = any(ca['is_class_teacher'] for ca in class_assignments)
            is_subject_only_teacher = not is_actual_class_teacher and len(class_assignments) > 0

            # Count totals
            total_classes = len(class_assignments)
            total_subjects = sum(len(ca['subjects']) for ca in class_assignments)

            return {
                'teacher': teacher,
                'is_actual_class_teacher': is_actual_class_teacher,
                'is_subject_only_teacher': is_subject_only_teacher,
                'can_access_portal': len(class_assignments) > 0,
                'class_assignments': class_assignments,
                'total_classes': total_classes,
                'total_subjects': total_subjects,
                'portal_type': 'Class Teacher' if is_actual_class_teacher else 'Subject Teacher'
            }

        except Exception as e:
            print(f"Error getting teacher portal summary: {str(e)}")
            return {'error': str(e)}
