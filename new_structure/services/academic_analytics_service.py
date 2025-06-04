"""
Academic Performance Analytics Service for Hillview School Management System.
Provides comprehensive analytics for student performance and subject metrics.
"""

from sqlalchemy import func, desc, asc, and_, or_
from ..models import Student, Mark, Subject, Grade, Stream, Term, AssessmentType, TeacherSubjectAssignment
from ..extensions import db
from ..services.cache_service import cache_analytics, get_cached_analytics, invalidate_analytics_cache
from typing import Dict, List, Optional, Tuple, Any
import time


class AcademicAnalyticsService:
    """
    Service for generating academic performance analytics and insights.
    Optimized for performance with caching and efficient database queries.
    """
    
    @classmethod
    def get_top_performers(cls, grade_id: Optional[int] = None, stream_id: Optional[int] = None,
                          term_id: Optional[int] = None, assessment_type_id: Optional[int] = None,
                          limit: int = 5, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get top performing students for specified grade/stream.
        
        Args:
            grade_id: Grade ID to filter by
            stream_id: Stream ID to filter by (None for grade-level analysis)
            term_id: Term ID to filter by (None for current term)
            assessment_type_id: Assessment type ID to filter by (None for all assessments)
            limit: Number of top performers to return (default: 5)
            use_cache: Whether to use cached results (default: True)
            
        Returns:
            Dictionary containing top performers and metadata
        """
        try:
            # Generate cache key
            cache_key = f"top_performers_{grade_id}_{stream_id}_{term_id}_{assessment_type_id}_{limit}"
            
            # Check cache first
            if use_cache:
                cached_result = get_cached_analytics(cache_key)
                if cached_result:
                    return cached_result
            
            # Build base query for student averages
            query = db.session.query(
                Student.id,
                Student.name,
                Student.admission_number,
                func.avg(Mark.percentage).label('average_percentage'),
                func.count(Mark.id).label('total_marks'),
                func.min(Mark.percentage).label('min_percentage'),
                func.max(Mark.percentage).label('max_percentage')
            ).join(Mark, Student.id == Mark.student_id)
            
            # Apply filters
            if grade_id:
                query = query.join(Stream, Student.stream_id == Stream.id).filter(Stream.grade_id == grade_id)
            
            if stream_id:
                query = query.filter(Student.stream_id == stream_id)
            
            if term_id:
                query = query.filter(Mark.term_id == term_id)
            
            if assessment_type_id:
                query = query.filter(Mark.assessment_type_id == assessment_type_id)
            
            # Group by student and order by average
            query = query.group_by(Student.id, Student.name, Student.admission_number)
            query = query.having(func.count(Mark.id) >= 3)  # Minimum 3 marks for ranking
            query = query.order_by(desc('average_percentage'))
            query = query.limit(limit)
            
            # Execute query
            results = query.all()
            
            # Format results
            top_performers = []
            for i, result in enumerate(results, 1):
                performer = {
                    'rank': i,
                    'student_id': result.id,
                    'name': result.name,
                    'admission_number': result.admission_number,
                    'average_percentage': round(result.average_percentage, 2),
                    'total_marks': result.total_marks,
                    'min_percentage': round(result.min_percentage, 2),
                    'max_percentage': round(result.max_percentage, 2),
                    'performance_category': cls._get_performance_category(result.average_percentage),
                    'grade_letter': cls._get_grade_letter(result.average_percentage)
                }
                top_performers.append(performer)
            
            # Get context information
            context = cls._get_context_info(grade_id, stream_id, term_id, assessment_type_id)
            
            result_data = {
                'top_performers': top_performers,
                'context': context,
                'total_students_analyzed': len(results),
                'generated_at': time.time()
            }
            
            # Cache the result
            if use_cache:
                cache_analytics(cache_key, result_data, expiry=1800)  # 30 minutes
            
            return result_data
            
        except Exception as e:
            print(f"Error getting top performers: {e}")
            return {
                'top_performers': [],
                'context': {},
                'total_students_analyzed': 0,
                'error': str(e)
            }
    
    @classmethod
    def get_subject_performance_analytics(cls, grade_id: Optional[int] = None, stream_id: Optional[int] = None,
                                        term_id: Optional[int] = None, assessment_type_id: Optional[int] = None,
                                        use_cache: bool = True) -> Dict[str, Any]:
        """
        Get subject performance analytics including top and least performing subjects.
        
        Args:
            grade_id: Grade ID to filter by
            stream_id: Stream ID to filter by
            term_id: Term ID to filter by
            assessment_type_id: Assessment type ID to filter by
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary containing subject performance analytics
        """
        try:
            # Generate cache key
            cache_key = f"subject_analytics_{grade_id}_{stream_id}_{term_id}_{assessment_type_id}"
            
            # Check cache first
            if use_cache:
                cached_result = get_cached_analytics(cache_key)
                if cached_result:
                    return cached_result
            
            # Build query for subject averages
            query = db.session.query(
                Subject.id,
                Subject.name,
                func.avg(Mark.percentage).label('average_percentage'),
                func.count(Mark.id).label('total_marks'),
                func.min(Mark.percentage).label('min_percentage'),
                func.max(Mark.percentage).label('max_percentage'),
                func.count(func.distinct(Mark.student_id)).label('student_count')
            ).join(Mark, Subject.id == Mark.subject_id)
            
            # Apply filters
            if grade_id or stream_id:
                query = query.join(Student, Mark.student_id == Student.id)
                
                if grade_id:
                    query = query.join(Stream, Student.stream_id == Stream.id).filter(Stream.grade_id == grade_id)
                
                if stream_id:
                    query = query.filter(Student.stream_id == stream_id)
            
            if term_id:
                query = query.filter(Mark.term_id == term_id)
            
            if assessment_type_id:
                query = query.filter(Mark.assessment_type_id == assessment_type_id)
            
            # Group by subject
            query = query.group_by(Subject.id, Subject.name)
            query = query.having(func.count(Mark.id) >= 5)  # Minimum 5 marks for analysis
            
            # Execute query
            results = query.all()
            
            if not results:
                return {
                    'subject_analytics': [],
                    'top_subject': None,
                    'least_performing_subject': None,
                    'context': cls._get_context_info(grade_id, stream_id, term_id, assessment_type_id),
                    'total_subjects_analyzed': 0
                }
            
            # Format results and sort
            subject_analytics = []
            for result in results:
                analytics = {
                    'subject_id': result.id,
                    'subject_name': result.name,
                    'average_percentage': round(result.average_percentage, 2),
                    'total_marks': result.total_marks,
                    'student_count': result.student_count,
                    'min_percentage': round(result.min_percentage, 2),
                    'max_percentage': round(result.max_percentage, 2),
                    'performance_category': cls._get_performance_category(result.average_percentage),
                    'grade_letter': cls._get_grade_letter(result.average_percentage)
                }
                subject_analytics.append(analytics)
            
            # Sort by average percentage
            subject_analytics.sort(key=lambda x: x['average_percentage'], reverse=True)
            
            # Identify top and least performing subjects
            top_subject = subject_analytics[0] if subject_analytics else None
            least_performing_subject = subject_analytics[-1] if subject_analytics else None
            
            result_data = {
                'subject_analytics': subject_analytics,
                'top_subject': top_subject,
                'least_performing_subject': least_performing_subject,
                'context': cls._get_context_info(grade_id, stream_id, term_id, assessment_type_id),
                'total_subjects_analyzed': len(subject_analytics),
                'generated_at': time.time()
            }
            
            # Cache the result
            if use_cache:
                cache_analytics(cache_key, result_data, expiry=1800)  # 30 minutes
            
            return result_data
            
        except Exception as e:
            print(f"Error getting subject analytics: {e}")
            return {
                'subject_analytics': [],
                'top_subject': None,
                'least_performing_subject': None,
                'context': {},
                'total_subjects_analyzed': 0,
                'error': str(e)
            }
    
    @classmethod
    def get_comprehensive_analytics(cls, grade_id: Optional[int] = None, stream_id: Optional[int] = None,
                                  term_id: Optional[int] = None, assessment_type_id: Optional[int] = None,
                                  top_performers_limit: int = 5) -> Dict[str, Any]:
        """
        Get comprehensive analytics combining top performers and subject analytics.
        
        Args:
            grade_id: Grade ID to filter by
            stream_id: Stream ID to filter by
            term_id: Term ID to filter by
            assessment_type_id: Assessment type ID to filter by
            top_performers_limit: Number of top performers to include
            
        Returns:
            Dictionary containing comprehensive analytics
        """
        try:
            # Get top performers
            top_performers_data = cls.get_top_performers(
                grade_id=grade_id,
                stream_id=stream_id,
                term_id=term_id,
                assessment_type_id=assessment_type_id,
                limit=top_performers_limit
            )
            
            # Get subject analytics
            subject_analytics_data = cls.get_subject_performance_analytics(
                grade_id=grade_id,
                stream_id=stream_id,
                term_id=term_id,
                assessment_type_id=assessment_type_id
            )
            
            # Combine results
            comprehensive_data = {
                'top_performers': top_performers_data.get('top_performers', []),
                'subject_analytics': subject_analytics_data.get('subject_analytics', []),
                'top_subject': subject_analytics_data.get('top_subject'),
                'least_performing_subject': subject_analytics_data.get('least_performing_subject'),
                'context': top_performers_data.get('context', {}),
                'summary': {
                    'total_students_analyzed': top_performers_data.get('total_students_analyzed', 0),
                    'total_subjects_analyzed': subject_analytics_data.get('total_subjects_analyzed', 0),
                    'has_sufficient_data': (
                        top_performers_data.get('total_students_analyzed', 0) >= 3 and
                        subject_analytics_data.get('total_subjects_analyzed', 0) >= 2
                    )
                },
                'generated_at': time.time()
            }
            
            return comprehensive_data
            
        except Exception as e:
            print(f"Error getting comprehensive analytics: {e}")
            return {
                'top_performers': [],
                'subject_analytics': [],
                'top_subject': None,
                'least_performing_subject': None,
                'context': {},
                'summary': {
                    'total_students_analyzed': 0,
                    'total_subjects_analyzed': 0,
                    'has_sufficient_data': False
                },
                'error': str(e)
            }
    
    @staticmethod
    def _get_performance_category(percentage: float) -> str:
        """Get performance category based on percentage."""
        if percentage >= 90:
            return 'Excellent'
        elif percentage >= 80:
            return 'Very Good'
        elif percentage >= 70:
            return 'Good'
        elif percentage >= 60:
            return 'Satisfactory'
        elif percentage >= 50:
            return 'Needs Improvement'
        else:
            return 'Below Expectations'
    
    @staticmethod
    def _get_grade_letter(percentage: float) -> str:
        """Get grade letter based on percentage."""
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        elif percentage >= 50:
            return 'E'
        else:
            return 'F'
    
    @staticmethod
    def _get_context_info(grade_id: Optional[int], stream_id: Optional[int],
                         term_id: Optional[int], assessment_type_id: Optional[int]) -> Dict[str, Any]:
        """Get context information for the analytics."""
        context = {}
        
        try:
            if grade_id:
                grade = Grade.query.get(grade_id)
                context['grade'] = grade.name if grade else f"Grade {grade_id}"
            
            if stream_id:
                stream = Stream.query.get(stream_id)
                context['stream'] = stream.name if stream else f"Stream {stream_id}"
            
            if term_id:
                term = Term.query.get(term_id)
                context['term'] = term.name if term else f"Term {term_id}"
            
            if assessment_type_id:
                assessment_type = AssessmentType.query.get(assessment_type_id)
                context['assessment_type'] = assessment_type.name if assessment_type else f"Assessment {assessment_type_id}"
            
        except Exception as e:
            print(f"Error getting context info: {e}")
        
        return context
