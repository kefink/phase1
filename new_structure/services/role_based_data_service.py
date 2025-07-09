"""
Role-Based Data Service for the Hillview School Management System.
Provides filtered data based on user roles and permissions.
"""
from ..models import Teacher, TeacherSubjectAssignment, Subject, Grade, Stream, Student
from ..extensions import db
from sqlalchemy import and_, or_


class RoleBasedDataService:
    """Service for providing role-based filtered data."""
    
    @staticmethod
    def get_teacher_assignments_summary(teacher_id, role):
        """
        Get a comprehensive summary of teacher assignments based on role.
        
        Args:
            teacher_id: ID of the teacher
            role: Role of the teacher ('teacher', 'classteacher', 'headteacher')
            
        Returns:
            Dictionary containing assignment summary data
        """
        try:
            teacher = Teacher.query.get(teacher_id)
            if not teacher:
                return {'error': 'Teacher not found'}
            
            # Get all assignments for this teacher
            teacher_assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id).all()
            
            # Initialize summary data
            summary = {
                'teacher': teacher,
                'role': role,
                'class_teacher_assignments': [],
                'subject_assignments': [],
                'total_classes_managed': 0,
                'total_subjects_taught': 0,
                'grades_involved': set(),
                'streams_involved': set(),
                'subjects_involved': set()
            }
            
            # Process assignments based on role
            if role == 'headteacher':
                # Headteacher sees everything
                summary.update(RoleBasedDataService._get_headteacher_summary())
                
            elif role == 'classteacher':
                # Class teacher sees their classes + all their subject assignments
                summary.update(RoleBasedDataService._get_classteacher_summary(teacher_assignments))
                
            elif role == 'teacher':
                # Subject teacher sees only their subject assignments
                summary.update(RoleBasedDataService._get_subject_teacher_summary(teacher_assignments))
            
            return summary
            
        except Exception as e:
            return {'error': f'Error getting teacher assignments: {str(e)}'}
    
    @staticmethod
    def _get_headteacher_summary():
        """Get summary data for headteacher (all data)."""
        try:
            all_assignments = TeacherSubjectAssignment.query.all()
            
            class_assignments = []
            subject_assignments = []
            
            for assignment in all_assignments:
                assignment_data = RoleBasedDataService._format_assignment(assignment)
                
                if assignment.is_class_teacher:
                    class_assignments.append(assignment_data)
                
                subject_assignments.append(assignment_data)
            
            return {
                'class_teacher_assignments': class_assignments,
                'subject_assignments': subject_assignments,
                'total_classes_managed': len(class_assignments),
                'total_subjects_taught': len(subject_assignments),
                'can_manage_all': True
            }
            
        except Exception as e:
            return {'error': f'Error getting headteacher summary: {str(e)}'}
    
    @staticmethod
    def _get_classteacher_summary(teacher_assignments):
        """Get summary data for class teacher."""
        try:
            class_assignments = []
            subject_assignments = []
            grades_involved = set()
            streams_involved = set()
            subjects_involved = set()

            # Track unique class assignments to avoid duplicates
            unique_class_assignments = {}

            for assignment in teacher_assignments:
                assignment_data = RoleBasedDataService._format_assignment(assignment)

                # Track involvement
                if assignment.grade:
                    grades_involved.add(assignment.grade.name)
                if assignment.stream:
                    streams_involved.add(assignment.stream.name)
                if assignment.subject:
                    subjects_involved.add(assignment.subject.name)

                # Separate class teacher assignments (deduplicate by grade+stream)
                if assignment.is_class_teacher:
                    class_key = f"{assignment_data['grade_level']}_{assignment_data['stream_name'] or 'None'}"
                    if class_key not in unique_class_assignments:
                        unique_class_assignments[class_key] = assignment_data

                # All assignments are subject assignments for class teachers
                subject_assignments.append(assignment_data)

            # Convert unique class assignments to list
            class_assignments = list(unique_class_assignments.values())
            
            return {
                'class_teacher_assignments': class_assignments,
                'subject_assignments': subject_assignments,
                'total_classes_managed': len(class_assignments),
                'total_subjects_taught': len(subject_assignments),
                'grades_involved': list(grades_involved),
                'streams_involved': list(streams_involved),
                'subjects_involved': list(subjects_involved),
                'can_manage_classes': len(class_assignments) > 0
            }
            
        except Exception as e:
            return {'error': f'Error getting classteacher summary: {str(e)}'}
    
    @staticmethod
    def _get_subject_teacher_summary(teacher_assignments):
        """Get summary data for subject teacher (includes both subject and class teacher assignments)."""
        try:
            subject_assignments = []
            class_assignments = []
            unique_class_assignments = {}
            grades_involved = set()
            streams_involved = set()
            subjects_involved = set()

            for assignment in teacher_assignments:
                assignment_data = RoleBasedDataService._format_assignment(assignment)

                # Track involvement
                if assignment.grade:
                    grades_involved.add(assignment.grade.name)
                if assignment.stream:
                    streams_involved.add(assignment.stream.name)
                if assignment.subject:
                    subjects_involved.add(assignment.subject.name)

                # Separate class teacher assignments (deduplicate by grade+stream)
                if assignment.is_class_teacher:
                    class_key = f"{assignment_data['grade_level']}_{assignment_data['stream_name'] or 'None'}"
                    if class_key not in unique_class_assignments:
                        unique_class_assignments[class_key] = assignment_data

                # All assignments are subject assignments
                subject_assignments.append(assignment_data)

            # Convert unique class assignments to list
            class_assignments = list(unique_class_assignments.values())

            return {
                'class_teacher_assignments': class_assignments,
                'subject_assignments': subject_assignments,
                'total_classes_managed': len(class_assignments),
                'total_subjects_taught': len(subject_assignments),
                'grades_involved': list(grades_involved),
                'streams_involved': list(streams_involved),
                'subjects_involved': list(subjects_involved),
                'can_manage_classes': len(class_assignments) > 0
            }

        except Exception as e:
            return {'error': f'Error getting subject teacher summary: {str(e)}'}
    
    @staticmethod
    def _format_assignment(assignment):
        """Format assignment data for display."""
        try:
            return {
                'id': assignment.id,
                'teacher_id': assignment.teacher_id,
                'teacher_username': assignment.teacher.username if assignment.teacher else 'Unknown',
                'teacher_full_name': assignment.teacher.full_name if assignment.teacher and assignment.teacher.full_name else assignment.teacher.username if assignment.teacher else 'Unknown',
                'subject_id': assignment.subject_id,
                'subject_name': assignment.subject.name if assignment.subject else 'Unknown Subject',
                'grade_id': assignment.grade_id,
                'grade_level': assignment.grade.name if assignment.grade else 'Unknown Grade',
                'stream_id': assignment.stream_id,
                'stream_name': assignment.stream.name if assignment.stream else None,
                'is_class_teacher': assignment.is_class_teacher,
                'education_level': RoleBasedDataService._get_education_level(assignment.grade.name if assignment.grade else '')
            }
        except Exception as e:
            return {
                'id': assignment.id if assignment else 0,
                'error': f'Error formatting assignment: {str(e)}'
            }
    
    @staticmethod
    def _get_education_level(grade_name):
        """Get education level from grade name."""
        if grade_name in ['Grade 1', 'Grade 2', 'Grade 3']:
            return 'lower_primary'
        elif grade_name in ['Grade 4', 'Grade 5', 'Grade 6']:
            return 'upper_primary'
        elif grade_name in ['Grade 7', 'Grade 8', 'Grade 9']:
            return 'junior_secondary'
        else:
            return 'unknown'
    
    @staticmethod
    def get_accessible_subjects(teacher_id, role):
        """
        Get subjects that a teacher can access based on their role.
        
        Args:
            teacher_id: ID of the teacher
            role: Role of the teacher
            
        Returns:
            List of subject objects the teacher can access
        """
        try:
            if role == 'headteacher':
                # Headteacher can access all subjects
                return Subject.query.all()
            
            elif role in ['teacher', 'classteacher']:
                # Get subjects from teacher's assignments
                assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id).all()
                subject_ids = [assignment.subject_id for assignment in assignments]
                
                if subject_ids:
                    return Subject.query.filter(Subject.id.in_(subject_ids)).all()
                else:
                    return []
            
            return []
            
        except Exception as e:
            print(f"Error getting accessible subjects: {str(e)}")
            return []
    
    @staticmethod
    def get_accessible_grades(teacher_id, role):
        """
        Get grades that a teacher can access based on their role.
        
        Args:
            teacher_id: ID of the teacher
            role: Role of the teacher
            
        Returns:
            List of grade objects the teacher can access
        """
        try:
            if role == 'headteacher':
                # Headteacher can access all grades
                return Grade.query.all()
            
            elif role in ['teacher', 'classteacher']:
                # Get grades from teacher's assignments
                assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id).all()
                grade_ids = [assignment.grade_id for assignment in assignments]
                
                if grade_ids:
                    return Grade.query.filter(Grade.id.in_(grade_ids)).all()
                else:
                    return []
            
            return []
            
        except Exception as e:
            print(f"Error getting accessible grades: {str(e)}")
            return []
    
    @staticmethod
    def get_accessible_streams(teacher_id, role):
        """
        Get streams that a teacher can access based on their role.
        
        Args:
            teacher_id: ID of the teacher
            role: Role of the teacher
            
        Returns:
            List of stream objects the teacher can access
        """
        try:
            if role == 'headteacher':
                # Headteacher can access all streams
                return Stream.query.all()
            
            elif role in ['teacher', 'classteacher']:
                # Get streams from teacher's assignments
                assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id).all()
                stream_ids = [assignment.stream_id for assignment in assignments if assignment.stream_id]
                
                if stream_ids:
                    return Stream.query.filter(Stream.id.in_(stream_ids)).all()
                else:
                    return []
            
            return []
            
        except Exception as e:
            print(f"Error getting accessible streams: {str(e)}")
            return []
