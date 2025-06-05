"""
Analytics API routes for Academic Performance Analytics Dashboard.
Provides REST API endpoints for analytics data.
"""

from flask import Blueprint, request, jsonify, session
from ..services.academic_analytics_service import AcademicAnalyticsService
from ..services.role_based_data_service import RoleBasedDataService
from ..services import is_authenticated, get_role
from ..models import Term, AssessmentType, Grade, Stream
from functools import wraps

# Create analytics API blueprint
analytics_api_bp = Blueprint('analytics_api', __name__, url_prefix='/api/analytics')


def analytics_required(f):
    """Decorator to ensure user is authenticated and has analytics access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session):
            return jsonify({'success': False, 'message': 'Authentication required'}), 401

        role = get_role(session)
        if role not in ['headteacher', 'classteacher']:
            return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403

        return f(*args, **kwargs)
    return decorated_function


@analytics_api_bp.route('/top_performers')
@analytics_required
def get_top_performers():
    """Get top performing students based on filters and user permissions."""
    try:
        # Get query parameters
        grade_id = request.args.get('grade_id', type=int)
        stream_id = request.args.get('stream_id', type=int)
        term_id = request.args.get('term_id', type=int)
        assessment_type_id = request.args.get('assessment_type_id', type=int)
        limit = request.args.get('limit', 5, type=int)
        
        # Apply role-based filtering
        role = get_role(session)
        teacher_id = session.get('teacher_id')
        
        if role == 'classteacher':
            # Classteachers can only see analytics for their assigned classes
            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, 'classteacher')

            if 'error' in assignment_summary:
                return jsonify({
                    'success': True,
                    'top_performers': [],
                    'message': assignment_summary['error']
                })

            assigned_classes = assignment_summary.get('class_teacher_assignments', [])
            if not assigned_classes:
                return jsonify({
                    'success': True,
                    'top_performers': [],
                    'message': 'No assigned classes found'
                })

            # If no specific grade/stream provided, use first assigned class
            if not grade_id and not stream_id and assigned_classes:
                first_class = assigned_classes[0]
                grade_id = first_class.get('grade_id')
                stream_id = first_class.get('stream_id')
        
        # Get top performers data
        result = AcademicAnalyticsService.get_top_performers(
            grade_id=grade_id,
            stream_id=stream_id,
            term_id=term_id,
            assessment_type_id=assessment_type_id,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'top_performers': result.get('top_performers', []),
            'context': result.get('context', {}),
            'total_students_analyzed': result.get('total_students_analyzed', 0)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting top performers: {str(e)}'
        }), 500


@analytics_api_bp.route('/subject_performance')
@analytics_required
def get_subject_performance():
    """Get subject performance analytics based on filters and user permissions."""
    try:
        # Get query parameters
        grade_id = request.args.get('grade_id', type=int)
        stream_id = request.args.get('stream_id', type=int)
        term_id = request.args.get('term_id', type=int)
        assessment_type_id = request.args.get('assessment_type_id', type=int)
        
        # Apply role-based filtering
        role = get_role(session)
        teacher_id = session.get('teacher_id')

        if role == 'classteacher':
            # Classteachers can only see analytics for their assigned classes
            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, 'classteacher')

            if 'error' in assignment_summary:
                return jsonify({
                    'success': True,
                    'subject_analytics': [],
                    'top_subject': None,
                    'least_performing_subject': None,
                    'message': assignment_summary['error']
                })

            assigned_classes = assignment_summary.get('class_teacher_assignments', [])
            if not assigned_classes:
                return jsonify({
                    'success': True,
                    'subject_analytics': [],
                    'top_subject': None,
                    'least_performing_subject': None,
                    'message': 'No assigned classes found'
                })

            # If no specific grade/stream provided, use first assigned class
            if not grade_id and not stream_id and assigned_classes:
                first_class = assigned_classes[0]
                grade_id = first_class.get('grade_id')
                stream_id = first_class.get('stream_id')
        
        # Get subject performance data
        result = AcademicAnalyticsService.get_subject_performance_analytics(
            grade_id=grade_id,
            stream_id=stream_id,
            term_id=term_id,
            assessment_type_id=assessment_type_id
        )
        
        return jsonify({
            'success': True,
            'subject_analytics': result.get('subject_analytics', []),
            'top_subject': result.get('top_subject'),
            'least_performing_subject': result.get('least_performing_subject'),
            'context': result.get('context', {}),
            'total_subjects_analyzed': result.get('total_subjects_analyzed', 0)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting subject performance: {str(e)}'
        }), 500


@analytics_api_bp.route('/comprehensive')
@analytics_required
def get_comprehensive_analytics():
    """Get comprehensive analytics including top performers and subject performance."""
    try:
        # Get query parameters
        grade_id = request.args.get('grade_id', type=int)
        stream_id = request.args.get('stream_id', type=int)
        term_id = request.args.get('term_id', type=int)
        assessment_type_id = request.args.get('assessment_type_id', type=int)
        top_performers_limit = request.args.get('limit', 5, type=int)
        
        # Apply role-based filtering
        role = get_role(session)
        teacher_id = session.get('teacher_id')

        if role == 'classteacher':
            # Classteachers can only see analytics for their assigned classes
            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, 'classteacher')

            if 'error' in assignment_summary:
                return jsonify({
                    'success': True,
                    'analytics': {
                        'top_performers': [],
                        'subject_analytics': [],
                        'top_subject': None,
                        'least_performing_subject': None,
                        'context': {},
                        'summary': {
                            'total_students_analyzed': 0,
                            'total_subjects_analyzed': 0,
                            'has_sufficient_data': False
                        }
                    },
                    'message': assignment_summary['error']
                })

            assigned_classes = assignment_summary.get('class_teacher_assignments', [])
            if not assigned_classes:
                return jsonify({
                    'success': True,
                    'analytics': {
                        'top_performers': [],
                        'subject_analytics': [],
                        'top_subject': None,
                        'least_performing_subject': None,
                        'context': {},
                        'summary': {
                            'total_students_analyzed': 0,
                            'total_subjects_analyzed': 0,
                            'has_sufficient_data': False
                        }
                    },
                    'message': 'No assigned classes found'
                })

            # If no specific grade/stream provided, use first assigned class
            if not grade_id and not stream_id and assigned_classes:
                first_class = assigned_classes[0]
                grade_id = first_class.get('grade_id')
                stream_id = first_class.get('stream_id')
        
        # Get comprehensive analytics data
        result = AcademicAnalyticsService.get_comprehensive_analytics(
            grade_id=grade_id,
            stream_id=stream_id,
            term_id=term_id,
            assessment_type_id=assessment_type_id,
            top_performers_limit=top_performers_limit
        )
        
        return jsonify({
            'success': True,
            'analytics': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting comprehensive analytics: {str(e)}'
        }), 500


@analytics_api_bp.route('/context_options')
@analytics_required
def get_context_options():
    """Get available options for analytics filters."""
    try:
        role = get_role(session)
        teacher_id = session.get('teacher_id')
        
        # Get terms
        terms = Term.query.all()
        terms_data = [{
            'id': term.id,
            'name': term.name,
            'is_current': term.is_current
        } for term in terms]
        
        # Get assessment types
        assessment_types = AssessmentType.query.all()
        assessment_types_data = [{
            'id': at.id,
            'name': at.name
        } for at in assessment_types]
        
        # Get grades and streams based on role
        grades_data = []
        streams_data = []
        
        if role == 'headteacher':
            # Headteachers can see all grades and streams
            grades = Grade.query.all()
            grades_data = [{
                'id': grade.id,
                'name': grade.name
            } for grade in grades]
            
            streams = Stream.query.all()
            streams_data = [{
                'id': stream.id,
                'name': stream.name,
                'grade_id': stream.grade_id
            } for stream in streams]
            
        elif role == 'classteacher':
            # Classteachers can only see their assigned grades and streams
            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, 'classteacher')

            if 'error' not in assignment_summary:
                assigned_classes = assignment_summary.get('class_teacher_assignments', [])

                # Extract unique grades and streams from assignments
                grade_ids = set()
                stream_ids = set()

                for assignment in assigned_classes:
                    if assignment.get('grade_id'):
                        grade_ids.add(assignment['grade_id'])
                    if assignment.get('stream_id'):
                        stream_ids.add(assignment['stream_id'])
            
            # Get grade data
            if grade_ids:
                grades = Grade.query.filter(Grade.id.in_(grade_ids)).all()
                grades_data = [{
                    'id': grade.id,
                    'name': grade.name
                } for grade in grades]
            
            # Get stream data
            if stream_ids:
                streams = Stream.query.filter(Stream.id.in_(stream_ids)).all()
                streams_data = [{
                    'id': stream.id,
                    'name': stream.name,
                    'grade_id': stream.grade_id
                } for stream in streams]
        
        return jsonify({
            'success': True,
            'options': {
                'terms': terms_data,
                'assessment_types': assessment_types_data,
                'grades': grades_data,
                'streams': streams_data
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting context options: {str(e)}'
        }), 500


@analytics_api_bp.route('/cache/invalidate', methods=['POST'])
@analytics_required
def invalidate_analytics_cache():
    """Invalidate analytics cache (admin function)."""
    try:
        role = get_role(session)
        if role != 'headteacher':
            return jsonify({
                'success': False,
                'message': 'Only headteachers can invalidate analytics cache'
            }), 403
        
        # Import cache service
        from ..services.cache_service import invalidate_analytics_cache
        
        # Invalidate all analytics cache
        invalidate_analytics_cache()
        
        return jsonify({
            'success': True,
            'message': 'Analytics cache invalidated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error invalidating cache: {str(e)}'
        }), 500


# Additional utility routes for supporting data
@analytics_api_bp.route('/terms')
@analytics_required
def get_terms():
    """Get available terms."""
    try:
        terms = Term.query.all()
        terms_data = [{
            'id': term.id,
            'name': term.name,
            'is_current': term.is_current
        } for term in terms]
        
        return jsonify({
            'success': True,
            'terms': terms_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting terms: {str(e)}'
        }), 500


@analytics_api_bp.route('/assessment_types')
@analytics_required
def get_assessment_types():
    """Get available assessment types."""
    try:
        assessment_types = AssessmentType.query.all()
        assessment_types_data = [{
            'id': at.id,
            'name': at.name
        } for at in assessment_types]
        
        return jsonify({
            'success': True,
            'assessment_types': assessment_types_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting assessment types: {str(e)}'
        }), 500


@analytics_api_bp.route('/grades')
@analytics_required
def get_grades():
    """Get available grades based on user permissions."""
    try:
        role = get_role(session)
        teacher_id = session.get('teacher_id')

        if role == 'headteacher':
            # Headteachers can see all grades
            grades = Grade.query.all()
        elif role == 'classteacher':
            # Classteachers can only see their assigned grades
            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, 'classteacher')

            if 'error' not in assignment_summary:
                assigned_classes = assignment_summary.get('class_teacher_assignments', [])
                grade_ids = set(assignment.get('grade_id') for assignment in assigned_classes if assignment.get('grade_id'))

                if grade_ids:
                    grades = Grade.query.filter(Grade.id.in_(grade_ids)).all()
                else:
                    grades = []
            else:
                grades = []
        else:
            grades = []
        
        grades_data = [{
            'id': grade.id,
            'name': grade.name
        } for grade in grades]
        
        return jsonify({
            'success': True,
            'grades': grades_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting grades: {str(e)}'
        }), 500
