"""
Analytics Service for Academic Performance Analytics
Provides comprehensive analytics data for both classteachers and headteachers
"""

from sqlalchemy import func, desc, and_, or_
from ..models.academic import Mark, Student, Subject, Grade, Stream, Term, AssessmentType
from ..models.user import Teacher
from ..models.assignment import TeacherSubjectAssignment
from ..extensions import db
from collections import defaultdict
import statistics

class AnalyticsService:
    """Service for generating academic performance analytics"""
    
    @staticmethod
    def get_classteacher_analytics(teacher_id):
        """
        Get analytics data for a specific classteacher based on their assignments
        """
        try:
            # Get teacher's assignments
            from .role_based_data_service import RoleBasedDataService
            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, 'classteacher')
            
            if 'error' in assignment_summary:
                return {'error': assignment_summary['error']}
            
            # Get assigned grades and streams
            assigned_grades = assignment_summary.get('grades_involved', [])
            assigned_streams = assignment_summary.get('streams_involved', [])
            assigned_subjects = assignment_summary.get('subjects_involved', [])
            
            # If no assignments, return empty analytics
            if not assigned_grades and not assigned_streams:
                return {
                    'summary': {
                        'students_analyzed': 0,
                        'subjects_analyzed': 0,
                        'best_subject_average': 0,
                        'top_student_average': 0
                    },
                    'top_students': [],
                    'subject_performance': [],
                    'grade_breakdown': [],
                    'recent_assessments': [],
                    'has_data': False
                }
            
            # Build query for marks based on teacher's assignments
            marks_query = db.session.query(Mark).join(Student).join(Stream).join(Grade).join(Subject)
            
            # Filter by assigned grades/streams
            if assigned_streams:
                stream_names = [s['name'] for s in assigned_streams]
                marks_query = marks_query.filter(Stream.name.in_(stream_names))
            elif assigned_grades:
                grade_names = [g['name'] for g in assigned_grades]
                marks_query = marks_query.filter(Grade.name.in_(grade_names))
            
            # Filter by assigned subjects if any
            if assigned_subjects:
                subject_names = [s['name'] for s in assigned_subjects]
                marks_query = marks_query.filter(Subject.name.in_(subject_names))
            
            marks = marks_query.all()
            
            if not marks:
                return {
                    'summary': {
                        'students_analyzed': 0,
                        'subjects_analyzed': 0,
                        'best_subject_average': 0,
                        'top_student_average': 0
                    },
                    'top_students': [],
                    'subject_performance': [],
                    'grade_breakdown': [],
                    'recent_assessments': [],
                    'has_data': False
                }
            
            # Process analytics data
            analytics_data = AnalyticsService._process_marks_data(marks)
            analytics_data['has_data'] = True
            analytics_data['assignment_summary'] = assignment_summary
            
            return analytics_data
            
        except Exception as e:
            print(f"Error in get_classteacher_analytics: {str(e)}")
            return {'error': f'Error generating analytics: {str(e)}'}
    
    @staticmethod
    def get_headteacher_analytics():
        """
        Get comprehensive school-wide analytics for headteacher
        """
        try:
            # Get all marks for school-wide analytics
            marks = Mark.query.join(Student).join(Stream).join(Grade).join(Subject).all()
            
            if not marks:
                return {
                    'summary': {
                        'total_students': 0,
                        'active_subjects': 0,
                        'school_average': 0,
                        'active_teachers': 0,
                        'total_assessments': 0
                    },
                    'grade_performance': [],
                    'subject_performance': [],
                    'top_students': [],
                    'recent_trends': [],
                    'teacher_performance': [],
                    'has_data': False
                }
            
            # Process school-wide analytics
            analytics_data = AnalyticsService._process_marks_data(marks, school_wide=True)
            
            # Add school-wide specific data
            analytics_data['summary']['total_students'] = Student.query.count()
            analytics_data['summary']['active_subjects'] = Subject.query.count()
            analytics_data['summary']['active_teachers'] = Teacher.query.filter(Teacher.role != 'headteacher').count()
            analytics_data['summary']['total_assessments'] = len(set((m.term_id, m.assessment_type_id) for m in marks))
            
            # Get grade-level performance
            analytics_data['grade_performance'] = AnalyticsService._get_grade_performance(marks)
            
            # Get teacher performance summary
            analytics_data['teacher_performance'] = AnalyticsService._get_teacher_performance()
            
            analytics_data['has_data'] = True
            
            return analytics_data
            
        except Exception as e:
            print(f"Error in get_headteacher_analytics: {str(e)}")
            return {'error': f'Error generating analytics: {str(e)}'}
    
    @staticmethod
    def _process_marks_data(marks, school_wide=False):
        """
        Process marks data to generate analytics insights
        """
        if not marks:
            return {}
        
        # Group marks by student
        student_marks = defaultdict(list)
        subject_marks = defaultdict(list)
        
        for mark in marks:
            student_key = f"{mark.student.name}_{mark.student.id}"
            student_marks[student_key].append(mark)
            subject_marks[mark.subject.name].append(mark)
        
        # Calculate student averages
        student_averages = []
        for student_key, marks_list in student_marks.items():
            student_name = marks_list[0].student.name
            student_grade = marks_list[0].student.stream.grade.name
            student_stream = marks_list[0].student.stream.name
            
            valid_marks = [m.percentage for m in marks_list if m.percentage is not None]
            if valid_marks:
                avg = round(statistics.mean(valid_marks), 1)
                student_averages.append({
                    'name': student_name,
                    'average': avg,
                    'grade': student_grade,
                    'stream': student_stream,
                    'subjects_count': len(valid_marks)
                })
        
        # Sort students by average
        student_averages.sort(key=lambda x: x['average'], reverse=True)
        
        # Calculate subject averages
        subject_averages = []
        for subject_name, marks_list in subject_marks.items():
            valid_marks = [m.percentage for m in marks_list if m.percentage is not None]
            if valid_marks:
                avg = round(statistics.mean(valid_marks), 1)
                subject_averages.append({
                    'name': subject_name,
                    'average': avg,
                    'students_count': len(set(m.student_id for m in marks_list)),
                    'total_marks': len(valid_marks)
                })
        
        # Sort subjects by average
        subject_averages.sort(key=lambda x: x['average'], reverse=True)
        
        # Get recent assessments
        recent_assessments = AnalyticsService._get_recent_assessments(marks)
        
        # Calculate summary statistics
        all_percentages = [m.percentage for m in marks if m.percentage is not None]
        
        summary = {
            'students_analyzed': len(student_marks),
            'subjects_analyzed': len(subject_marks),
            'best_subject_average': subject_averages[0]['average'] if subject_averages else 0,
            'top_student_average': student_averages[0]['average'] if student_averages else 0,
            'school_average': round(statistics.mean(all_percentages), 1) if all_percentages else 0
        }
        
        return {
            'summary': summary,
            'top_students': student_averages[:10],  # Top 10 students
            'subject_performance': subject_averages,
            'recent_assessments': recent_assessments,
            'grade_breakdown': AnalyticsService._get_grade_breakdown(marks)
        }
    
    @staticmethod
    def _get_recent_assessments(marks):
        """Get recent assessment data"""
        # Group by term and assessment type
        assessment_groups = defaultdict(list)
        
        for mark in marks:
            key = f"{mark.term.name}_{mark.assessment_type.name}"
            assessment_groups[key].append(mark)
        
        recent_assessments = []
        for key, marks_list in assessment_groups.items():
            term_name, assessment_name = key.split('_', 1)
            valid_marks = [m.percentage for m in marks_list if m.percentage is not None]
            
            if valid_marks:
                recent_assessments.append({
                    'term': term_name,
                    'assessment': assessment_name,
                    'average': round(statistics.mean(valid_marks), 1),
                    'students_count': len(set(m.student_id for m in marks_list)),
                    'date': max(m.created_at for m in marks_list if m.created_at).strftime('%Y-%m-%d')
                })
        
        # Sort by date (most recent first)
        recent_assessments.sort(key=lambda x: x['date'], reverse=True)
        return recent_assessments[:5]  # Last 5 assessments
    
    @staticmethod
    def _get_grade_breakdown(marks):
        """Get performance breakdown by grade"""
        grade_marks = defaultdict(list)
        
        for mark in marks:
            if mark.percentage is not None:
                grade_marks[mark.student.stream.grade.name].append(mark.percentage)
        
        grade_breakdown = []
        for grade_name, percentages in grade_marks.items():
            if percentages:
                grade_breakdown.append({
                    'grade': grade_name,
                    'average': round(statistics.mean(percentages), 1),
                    'students_count': len(set(mark.student_id for mark in marks if mark.student.stream.grade.name == grade_name)),
                    'total_marks': len(percentages)
                })
        
        grade_breakdown.sort(key=lambda x: x['grade'])
        return grade_breakdown
    
    @staticmethod
    def _get_grade_performance(marks):
        """Get detailed grade performance for headteacher"""
        return AnalyticsService._get_grade_breakdown(marks)
    
    @staticmethod
    def _get_teacher_performance():
        """Get teacher performance summary"""
        try:
            # Get teachers with their assignment counts
            teachers = db.session.query(Teacher).filter(Teacher.role != 'headteacher').all()
            
            teacher_performance = []
            for teacher in teachers:
                # Count subject assignments
                subject_count = db.session.query(TeacherSubjectAssignment).filter_by(teacher_id=teacher.id).count()
                
                # Get class teacher assignment
                class_assignment = "Yes" if teacher.stream_id else "No"
                
                teacher_performance.append({
                    'name': teacher.full_name or teacher.username,
                    'username': teacher.username,
                    'subjects_assigned': subject_count,
                    'class_teacher': class_assignment,
                    'status': 'Active' if subject_count > 0 or teacher.stream_id else 'Inactive'
                })
            
            return teacher_performance
            
        except Exception as e:
            print(f"Error getting teacher performance: {str(e)}")
            return []
