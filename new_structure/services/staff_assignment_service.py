"""
Staff Assignment Service for managing dynamic teacher assignments and report generation.
"""
from ..models import Teacher, TeacherSubjectAssignment, SchoolConfiguration, Grade, Stream, Subject
from ..extensions import db
from sqlalchemy import and_

class StaffAssignmentService:
    """Service for managing staff assignments and retrieving staff information for reports."""

    @staticmethod
    def get_class_teacher(grade, stream):
        """
        Get the class teacher for a specific grade and stream.

        Args:
            grade: Grade level (e.g., "Grade 1", "Grade 2")
            stream: Stream name (e.g., "Stream A", "Stream B")

        Returns:
            Teacher object or None if no class teacher assigned
        """
        try:
            # Get grade and stream objects
            grade_obj = Grade.query.filter_by(name=grade).first()
            stream_obj = Stream.query.filter_by(name=stream).first()

            if not grade_obj or not stream_obj:
                print(f"Grade or stream not found: {grade}, {stream}")
                return None

            # Find class teacher assignment
            assignment = TeacherSubjectAssignment.query.filter(
                and_(
                    TeacherSubjectAssignment.grade_id == grade_obj.id,
                    TeacherSubjectAssignment.stream_id == stream_obj.id,
                    TeacherSubjectAssignment.is_class_teacher == True
                )
            ).first()

            if assignment:
                print(f"Found class teacher assignment: {assignment.teacher.username} for {grade} {stream}")
                return assignment.teacher
            else:
                print(f"No class teacher assignment found for {grade} {stream}")
                # Try to find any teacher assigned to this grade/stream and check if they should be class teacher
                all_assignments = TeacherSubjectAssignment.query.filter(
                    and_(
                        TeacherSubjectAssignment.grade_id == grade_obj.id,
                        TeacherSubjectAssignment.stream_id == stream_obj.id
                    )
                ).all()
                print(f"Found {len(all_assignments)} total assignments for {grade} {stream}")
                for assign in all_assignments:
                    print(f"  - {assign.teacher.username} teaches {assign.subject.name}, is_class_teacher: {assign.is_class_teacher}")
                return None

        except Exception as e:
            print(f"Error getting class teacher: {str(e)}")
            return None

    @staticmethod
    def get_subject_teachers(grade, stream):
        """
        Get all subject teachers for a specific grade and stream.

        Args:
            grade: Grade level
            stream: Stream name

        Returns:
            Dictionary mapping subject names to teacher objects
        """
        try:
            # Get grade and stream objects
            grade_obj = Grade.query.filter_by(name=grade).first()
            stream_obj = Stream.query.filter_by(name=stream).first()

            if not grade_obj or not stream_obj:
                return {}

            # Get all subject assignments for this grade and stream
            assignments = TeacherSubjectAssignment.query.filter(
                and_(
                    TeacherSubjectAssignment.grade_id == grade_obj.id,
                    TeacherSubjectAssignment.stream_id == stream_obj.id
                )
            ).all()

            subject_teachers = {}
            for assignment in assignments:
                if assignment.subject and assignment.teacher:
                    subject_teachers[assignment.subject.name] = assignment.teacher

            return subject_teachers

        except Exception as e:
            print(f"Error getting subject teachers: {str(e)}")
            return {}

    @staticmethod
    def get_headteacher():
        """
        Get the current headteacher from school configuration.

        Returns:
            Teacher object or None if no headteacher assigned
        """
        try:
            config = SchoolConfiguration.get_config()
            # Check if dynamic headteacher_id field exists (after migration)
            if hasattr(config, 'headteacher_id') and config.headteacher_id:
                return Teacher.query.get(config.headteacher_id)
            # Fallback: try to find headteacher by role
            return Teacher.query.filter_by(role='headteacher').first()
        except Exception as e:
            print(f"Error getting headteacher: {str(e)}")
            return None

    @staticmethod
    def get_deputy_headteacher():
        """
        Get the current deputy headteacher from school configuration.

        Returns:
            Teacher object or None if no deputy headteacher assigned
        """
        try:
            config = SchoolConfiguration.get_config()
            # Check if dynamic deputy_headteacher_id field exists (after migration)
            if hasattr(config, 'deputy_headteacher_id') and config.deputy_headteacher_id:
                return Teacher.query.get(config.deputy_headteacher_id)
            # Fallback: return None for now (can be enhanced later)
            return None
        except Exception as e:
            print(f"Error getting deputy headteacher: {str(e)}")
            return None

    @staticmethod
    def assign_class_teacher(teacher_id, grade, stream):
        """
        Assign a teacher as class teacher for a specific grade and stream.

        Args:
            teacher_id: ID of the teacher to assign
            grade: Grade level
            stream: Stream name

        Returns:
            Boolean indicating success
        """
        try:
            # Get grade and stream objects
            grade_obj = Grade.query.filter_by(name=grade).first()
            stream_obj = Stream.query.filter_by(name=stream).first()
            teacher = Teacher.query.get(teacher_id)

            if not grade_obj or not stream_obj or not teacher:
                return False

            # Remove existing class teacher assignment for this grade/stream
            existing_assignment = TeacherSubjectAssignment.query.filter(
                and_(
                    TeacherSubjectAssignment.grade_id == grade_obj.id,
                    TeacherSubjectAssignment.stream_id == stream_obj.id,
                    TeacherSubjectAssignment.is_class_teacher == True
                )
            ).first()

            if existing_assignment:
                existing_assignment.is_class_teacher = False

            # Find or create assignment for the new class teacher
            # We'll assign them to a default subject (like Mathematics) if they don't have one
            default_subject = Subject.query.first()  # Get any subject as default

            assignment = TeacherSubjectAssignment.query.filter(
                and_(
                    TeacherSubjectAssignment.teacher_id == teacher_id,
                    TeacherSubjectAssignment.grade_id == grade_obj.id,
                    TeacherSubjectAssignment.stream_id == stream_obj.id
                )
            ).first()

            if not assignment and default_subject:
                assignment = TeacherSubjectAssignment(
                    teacher_id=teacher_id,
                    subject_id=default_subject.id,
                    grade_id=grade_obj.id,
                    stream_id=stream_obj.id,
                    is_class_teacher=True
                )
                db.session.add(assignment)
            elif assignment:
                assignment.is_class_teacher = True

            db.session.commit()
            return True

        except Exception as e:
            print(f"Error assigning class teacher: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def set_headteacher(teacher_id):
        """
        Set a teacher as the headteacher in school configuration.

        Args:
            teacher_id: ID of the teacher to set as headteacher

        Returns:
            Boolean indicating success
        """
        try:
            config = SchoolConfiguration.get_config()
            teacher = Teacher.query.get(teacher_id)

            if not teacher:
                return False

            config.headteacher_id = teacher_id
            config.headteacher_name = getattr(teacher, 'full_name', None) or teacher.username

            # Update teacher role
            teacher.role = 'headteacher'

            db.session.commit()
            return True

        except Exception as e:
            print(f"Error setting headteacher: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def set_deputy_headteacher(teacher_id):
        """
        Set a teacher as the deputy headteacher in school configuration.

        Args:
            teacher_id: ID of the teacher to set as deputy headteacher

        Returns:
            Boolean indicating success
        """
        try:
            config = SchoolConfiguration.get_config()
            teacher = Teacher.query.get(teacher_id)

            if not teacher:
                return False

            config.deputy_headteacher_id = teacher_id
            config.deputy_headteacher_name = getattr(teacher, 'full_name', None) or teacher.username

            db.session.commit()
            return True

        except Exception as e:
            print(f"Error setting deputy headteacher: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def get_report_staff_info(grade, stream):
        """
        Get comprehensive staff information for report generation.

        Args:
            grade: Grade level
            stream: Stream name

        Returns:
            Dictionary containing all staff information for reports
        """
        class_teacher = StaffAssignmentService.get_class_teacher(grade, stream)
        subject_teachers = StaffAssignmentService.get_subject_teachers(grade, stream)
        headteacher = StaffAssignmentService.get_headteacher()
        deputy_headteacher = StaffAssignmentService.get_deputy_headteacher()

        # Helper function to safely get teacher attributes
        def get_teacher_name(teacher):
            if not teacher:
                return 'Not Assigned'
            return getattr(teacher, 'full_name', None) or teacher.username

        def get_teacher_employee_id(teacher):
            if not teacher:
                return None
            return getattr(teacher, 'employee_id', None)

        def get_teacher_qualification(teacher):
            if not teacher:
                return None
            return getattr(teacher, 'qualification', None)

        return {
            'class_teacher': {
                'name': get_teacher_name(class_teacher),
                'employee_id': get_teacher_employee_id(class_teacher),
                'qualification': get_teacher_qualification(class_teacher)
            },
            'headteacher': {
                'name': get_teacher_name(headteacher),
                'employee_id': get_teacher_employee_id(headteacher)
            },
            'deputy_headteacher': {
                'name': get_teacher_name(deputy_headteacher),
                'employee_id': get_teacher_employee_id(deputy_headteacher)
            },
            'subject_teachers': {
                subject: {
                    'name': get_teacher_name(teacher),
                    'employee_id': get_teacher_employee_id(teacher),
                    'qualification': get_teacher_qualification(teacher)
                }
                for subject, teacher in subject_teachers.items()
            }
        }

    @staticmethod
    def fix_kevin_class_teacher_assignment():
        """
        Debug function to ensure Kevin is properly assigned as class teacher for Grade 9B.
        This should be called once to fix the assignment.
        """
        try:
            # Find Kevin
            kevin = Teacher.query.filter_by(username='kevin').first()
            if not kevin:
                print("Kevin not found in teachers table")
                return False

            # Find Grade 9
            grade_9 = Grade.query.filter_by(name='Grade 9').first()
            if not grade_9:
                print("Grade 9 not found")
                return False

            # Find Stream B
            stream_b = Stream.query.filter_by(name='B').first()
            if not stream_b:
                print("Stream B not found")
                return False

            print(f"Found Kevin (ID: {kevin.id}), Grade 9 (ID: {grade_9.id}), Stream B (ID: {stream_b.id})")

            # Check if Kevin has any assignments for Grade 9 Stream B
            existing_assignments = TeacherSubjectAssignment.query.filter(
                and_(
                    TeacherSubjectAssignment.teacher_id == kevin.id,
                    TeacherSubjectAssignment.grade_id == grade_9.id,
                    TeacherSubjectAssignment.stream_id == stream_b.id
                )
            ).all()

            print(f"Kevin has {len(existing_assignments)} existing assignments for Grade 9 Stream B")

            if existing_assignments:
                # Mark one of his assignments as class teacher
                assignment = existing_assignments[0]
                assignment.is_class_teacher = True
                print(f"Marked Kevin's {assignment.subject.name} assignment as class teacher")
            else:
                # Create a new assignment for Kevin as class teacher
                # Get a default subject (Mathematics)
                math_subject = Subject.query.filter_by(name='MATHEMATICS').first()
                if not math_subject:
                    math_subject = Subject.query.first()  # Get any subject

                if math_subject:
                    new_assignment = TeacherSubjectAssignment(
                        teacher_id=kevin.id,
                        subject_id=math_subject.id,
                        grade_id=grade_9.id,
                        stream_id=stream_b.id,
                        is_class_teacher=True
                    )
                    db.session.add(new_assignment)
                    print(f"Created new class teacher assignment for Kevin: {math_subject.name}")

            # Remove class teacher flag from any other teachers for Grade 9 Stream B
            other_class_teachers = TeacherSubjectAssignment.query.filter(
                and_(
                    TeacherSubjectAssignment.teacher_id != kevin.id,
                    TeacherSubjectAssignment.grade_id == grade_9.id,
                    TeacherSubjectAssignment.stream_id == stream_b.id,
                    TeacherSubjectAssignment.is_class_teacher == True
                )
            ).all()

            for assignment in other_class_teachers:
                assignment.is_class_teacher = False
                print(f"Removed class teacher flag from {assignment.teacher.username}")

            db.session.commit()
            print("✅ Kevin's class teacher assignment fixed successfully")
            return True

        except Exception as e:
            print(f"Error fixing Kevin's assignment: {str(e)}")
            db.session.rollback()
            return False
