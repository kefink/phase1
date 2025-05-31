"""
Collaborative Marks Service for managing multi-teacher marks upload workflow.
"""
from ..models.academic import SubjectMarksStatus, Mark, Subject, Grade, Stream, Term, AssessmentType, Student
from ..models.assignment import TeacherSubjectAssignment
from ..models.user import Teacher
from ..extensions import db
from sqlalchemy import and_


class CollaborativeMarksService:
    """Service for handling collaborative marks upload between subject teachers and class teachers."""

    @staticmethod
    def get_class_marks_status(grade_id, stream_id, term_id, assessment_type_id):
        """
        Get the marks upload status for all subjects in a class.

        Returns:
            dict: Status information for each subject
        """
        try:
            # Get all subjects for the grade's education level
            grade = Grade.query.get(grade_id)
            if not grade:
                return {"error": "Grade not found"}

            # Get subjects based on education level
            subjects = Subject.query.filter_by(education_level=grade.education_level).all()

            status_data = {
                'grade': grade.name,
                'stream': Stream.query.get(stream_id).name if stream_id else 'Unknown',
                'term': Term.query.get(term_id).name if term_id else 'Unknown',
                'assessment_type': AssessmentType.query.get(assessment_type_id).name if assessment_type_id else 'Unknown',
                'subjects': [],
                'overall_completion': 0,
                'total_subjects': len(subjects),
                'completed_subjects': 0,
                'can_generate_report': False
            }

            for subject in subjects:
                # Get or create status for this subject
                status = SubjectMarksStatus.query.filter_by(
                    grade_id=grade_id,
                    stream_id=stream_id,
                    subject_id=subject.id,
                    term_id=term_id,
                    assessment_type_id=assessment_type_id
                ).first()

                if not status:
                    # Create initial status
                    status = SubjectMarksStatus.update_status(
                        grade_id, stream_id, subject.id, term_id, assessment_type_id
                    )

                # Get assigned teacher for this subject
                assigned_teacher = TeacherSubjectAssignment.query.filter_by(
                    subject_id=subject.id,
                    grade_id=grade_id,
                    stream_id=stream_id
                ).first()

                subject_info = {
                    'id': subject.id,
                    'name': subject.name,
                    'is_uploaded': status.is_uploaded if status else False,
                    'completion_percentage': status.completion_percentage if status else 0,
                    'total_students': status.total_students if status else 0,
                    'students_with_marks': status.students_with_marks if status else 0,
                    'assigned_teacher': assigned_teacher.teacher.username if assigned_teacher and assigned_teacher.teacher else 'Unassigned',
                    'uploaded_by': status.uploaded_by.username if status and status.uploaded_by else None,
                    'upload_date': status.upload_date.strftime('%Y-%m-%d %H:%M') if status and status.upload_date else None,
                    'can_upload': True  # Will be refined based on teacher permissions
                }

                status_data['subjects'].append(subject_info)

                if status and status.is_uploaded:
                    status_data['completed_subjects'] += 1

            # Calculate overall completion
            if status_data['total_subjects'] > 0:
                status_data['overall_completion'] = (status_data['completed_subjects'] / status_data['total_subjects']) * 100
                status_data['can_generate_report'] = status_data['completed_subjects'] == status_data['total_subjects']

            return status_data

        except Exception as e:
            print(f"Error getting class marks status: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def can_teacher_upload_subject(teacher_id, subject_id, grade_id, stream_id):
        """
        Check if a teacher can upload marks for a specific subject.

        Returns:
            bool: True if teacher can upload marks
        """
        try:
            # Check if teacher is assigned to this subject
            assignment = TeacherSubjectAssignment.query.filter_by(
                teacher_id=teacher_id,
                subject_id=subject_id,
                grade_id=grade_id,
                stream_id=stream_id
            ).first()

            if assignment:
                return True

            # Check if teacher is class teacher for this class (can upload all subjects)
            class_teacher_assignment = TeacherSubjectAssignment.query.filter_by(
                teacher_id=teacher_id,
                grade_id=grade_id,
                stream_id=stream_id,
                is_class_teacher=True
            ).first()

            return class_teacher_assignment is not None

        except Exception as e:
            print(f"Error checking teacher upload permission: {str(e)}")
            return False

    @staticmethod
    def get_teacher_assigned_subjects_for_class(teacher_id, grade_id, stream_id):
        """
        Get subjects that a teacher can upload marks for in a specific class.

        Returns:
            list: Subject IDs that teacher can upload
        """
        try:
            # Get direct subject assignments
            subject_assignments = TeacherSubjectAssignment.query.filter_by(
                teacher_id=teacher_id,
                grade_id=grade_id,
                stream_id=stream_id
            ).all()

            subject_ids = [assignment.subject_id for assignment in subject_assignments]

            # If teacher is class teacher, they can upload all subjects
            is_class_teacher = any(assignment.is_class_teacher for assignment in subject_assignments)

            if is_class_teacher:
                # Get all subjects for the grade's education level
                grade = Grade.query.get(grade_id)
                if grade:
                    all_subjects = Subject.query.filter_by(education_level=grade.education_level).all()
                    subject_ids = [subject.id for subject in all_subjects]

            return subject_ids

        except Exception as e:
            print(f"Error getting teacher assigned subjects: {str(e)}")
            return []

    @staticmethod
    def update_marks_status_after_upload(grade_id, stream_id, subject_id, term_id, assessment_type_id, teacher_id):
        """
        Update marks status after a teacher uploads marks.

        Returns:
            dict: Updated status information
        """
        try:
            # Update the status
            status = SubjectMarksStatus.update_status(
                grade_id, stream_id, subject_id, term_id, assessment_type_id, teacher_id
            )

            if status:
                return {
                    'success': True,
                    'is_complete': status.is_uploaded,
                    'completion_percentage': status.completion_percentage,
                    'students_with_marks': status.students_with_marks,
                    'total_students': status.total_students
                }
            else:
                return {'success': False, 'error': 'Failed to update status'}

        except Exception as e:
            print(f"Error updating marks status: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_class_teacher_dashboard_data(teacher_id):
        """
        Get dashboard data for a class teacher showing all their classes and marks status.

        Returns:
            dict: Dashboard data with class information and marks status
        """
        try:
            # Get all classes where this teacher is class teacher
            class_assignments = TeacherSubjectAssignment.query.filter_by(
                teacher_id=teacher_id,
                is_class_teacher=True
            ).all()

            dashboard_data = {
                'classes': [],
                'total_classes': len(class_assignments),
                'classes_ready_for_reports': 0
            }

            for assignment in class_assignments:
                grade = assignment.grade
                stream = assignment.stream

                # Get latest term and assessment type (you might want to make this configurable)
                latest_term = Term.query.order_by(Term.id.desc()).first()
                latest_assessment = AssessmentType.query.order_by(AssessmentType.id.desc()).first()

                if latest_term and latest_assessment:
                    class_status = CollaborativeMarksService.get_class_marks_status(
                        grade.id, stream.id, latest_term.id, latest_assessment.id
                    )

                    class_info = {
                        'grade': grade.name,
                        'stream': stream.name,
                        'grade_id': grade.id,
                        'stream_id': stream.id,
                        'term_id': latest_term.id,
                        'assessment_type_id': latest_assessment.id,
                        'overall_completion': class_status.get('overall_completion', 0),
                        'completed_subjects': class_status.get('completed_subjects', 0),
                        'total_subjects': class_status.get('total_subjects', 0),
                        'can_generate_report': class_status.get('can_generate_report', False),
                        'subjects': class_status.get('subjects', [])
                    }

                    dashboard_data['classes'].append(class_info)

                    if class_info['can_generate_report']:
                        dashboard_data['classes_ready_for_reports'] += 1

            return dashboard_data

        except Exception as e:
            print(f"Error getting class teacher dashboard data: {str(e)}")
            return {'error': str(e)}
