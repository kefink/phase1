"""
Analytics API routes for Academic Performance Analytics Dashboard.
Provides REST API endpoints for analytics data.
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
from ..services.academic_analytics_service import AcademicAnalyticsService
from ..services.role_based_data_service import RoleBasedDataService
from ..services.report_based_analytics_service import ReportBasedAnalyticsService
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
        view_type = request.args.get('view_type', 'summary')  # 'summary' or 'detailed'
        
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
            limit=limit,
            view_type=view_type
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


@analytics_api_bp.route('/enhanced_subject_performance')
@analytics_required
def get_enhanced_subject_performance():
    """Get enhanced subject performance analytics with grade and stream comparisons."""
    try:
        # Get query parameters
        grade_id = request.args.get('grade_id', type=int)
        term_id = request.args.get('term_id', type=int)
        assessment_type_id = request.args.get('assessment_type_id', type=int)

        # Apply role-based filtering
        role = get_role(session)
        teacher_id = session.get('teacher_id')

        if role == 'classteacher':
            # Classteachers can only see analytics for their assigned classes
            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, 'classteacher')

            if not assignment_summary or not assignment_summary.get('has_assignments'):
                return jsonify({
                    'success': False,
                    'message': 'No class assignments found for this teacher'
                }), 403

            assigned_classes = assignment_summary.get('assigned_classes', [])

            # If no specific grade provided, use first assigned class
            if not grade_id and assigned_classes:
                first_class = assigned_classes[0]
                grade_id = first_class.get('grade_id')

        # Get enhanced subject performance data
        result = AcademicAnalyticsService.get_enhanced_subject_performance_analytics(
            grade_id=grade_id,
            term_id=term_id,
            assessment_type_id=assessment_type_id
        )

        return jsonify({
            'success': True,
            'grade_subject_analytics': result.get('grade_subject_analytics', {}),
            'subject_stream_comparisons': result.get('subject_stream_comparisons', {}),
            'context': result.get('context', {}),
            'total_grades_analyzed': result.get('total_grades_analyzed', 0)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting enhanced subject performance: {str(e)}'
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


@analytics_api_bp.route('/report_based')
@analytics_required
def get_report_based_analytics():
    """Get analytics based on classteacher-generated reports."""
    try:
        # Get query parameters
        grade_filter = request.args.get('grade')
        term_filter = request.args.get('term')
        assessment_filter = request.args.get('assessment_type')
        days_back = request.args.get('days_back', 30, type=int)

        # Apply role-based filtering
        role = get_role(session)
        teacher_id = session.get('teacher_id')

        # Get report-based analytics
        result = ReportBasedAnalyticsService.get_report_based_analytics(
            grade_filter=grade_filter,
            term_filter=term_filter,
            assessment_filter=assessment_filter,
            days_back=days_back
        )

        # Add role-specific context
        if role == 'classteacher':
            # Add teacher-specific information
            teacher_summary = ReportBasedAnalyticsService.get_teacher_report_summary(teacher_id)
            result['teacher_summary'] = teacher_summary

        return jsonify({
            'success': True,
            'analytics': result,
            'data_source': 'generated_reports',
            'role': role
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting report-based analytics: {str(e)}'
        }), 500


@analytics_api_bp.route('/available_reports')
@analytics_required
def get_available_reports():
    """Get list of available cached reports for analytics."""
    try:
        role = get_role(session)

        # Get available reports
        reports = ReportBasedAnalyticsService.get_available_reports()

        # Filter reports based on role if needed
        if role == 'classteacher':
            teacher_id = session.get('teacher_id')
            # In a full implementation, you would filter reports by teacher's assigned classes
            # For now, return all reports but add a note
            filtered_reports = reports  # TODO: Implement teacher-specific filtering
        else:
            filtered_reports = reports

        return jsonify({
            'success': True,
            'reports': filtered_reports,
            'total_reports': len(filtered_reports),
            'role': role
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting available reports: {str(e)}'
        }), 500


@analytics_api_bp.route('/dashboard_data')
@analytics_required
def get_dashboard_analytics():
    """Get analytics data optimized for dashboard display."""
    try:
        role = get_role(session)
        teacher_id = session.get('teacher_id')

        # Get dashboard-optimized analytics
        result = ReportBasedAnalyticsService.get_analytics_dashboard_data(
            role=role,
            teacher_id=teacher_id
        )

        return jsonify({
            'success': True,
            'dashboard_data': result,
            'role': role,
            'data_source': 'generated_reports'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting dashboard analytics: {str(e)}'
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


@analytics_api_bp.route('/delete_report', methods=['POST'])
@analytics_required
def delete_report_from_analytics():
    """Delete a report and its associated marks from analytics page."""
    try:
        # Get parameters
        grade = request.form.get('grade')
        stream = request.form.get('stream')
        term = request.form.get('term')
        assessment_type = request.form.get('assessment_type')

        if not all([grade, stream, term, assessment_type]):
            return jsonify({
                'success': False,
                'message': 'Missing required parameters'
            }), 400

        # Check permissions - only headteachers can delete from analytics
        role = get_role(session)
        is_headteacher = role == 'headteacher' or session.get('headteacher_universal_access')

        if not is_headteacher:
            return jsonify({
                'success': False,
                'message': 'Only headteachers can delete reports from analytics'
            }), 403

        # Import required models
        from ..models.academic import Mark, Student, Grade as GradeModel, Stream as StreamModel, Term as TermModel, AssessmentType
        from ..extensions import db

        # Extract stream letter from "Stream X" format
        stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream

        # Get the objects
        stream_obj = StreamModel.query.join(GradeModel).filter(
            GradeModel.name == grade,
            StreamModel.name == stream_letter
        ).first()
        term_obj = TermModel.query.filter_by(name=term).first()
        assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

        if not all([stream_obj, term_obj, assessment_type_obj]):
            return jsonify({
                'success': False,
                'message': 'Could not find specified grade, stream, term, or assessment type'
            }), 404

        # Delete all marks for this combination
        marks_to_delete = Mark.query.join(Student).filter(
            Student.stream_id == stream_obj.id,
            Mark.term_id == term_obj.id,
            Mark.assessment_type_id == assessment_type_obj.id
        ).all()

        deleted_count = len(marks_to_delete)

        for mark in marks_to_delete:
            db.session.delete(mark)

        # Commit the changes
        db.session.commit()

        # Invalidate cache for this combination
        from ..services.cache_service import invalidate_cache
        invalidate_cache(grade, stream, term, assessment_type)

        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} marks for {grade} {stream} in {term} {assessment_type}',
            'deleted_count': deleted_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting report: {str(e)}'
        }), 500


@analytics_api_bp.route('/delete_subject_marks', methods=['POST'])
@analytics_required
def delete_subject_marks():
    """Delete marks for a specific subject in a grade/stream/term/assessment combination."""
    try:
        # Get parameters
        grade = request.form.get('grade')
        stream = request.form.get('stream')
        term = request.form.get('term')
        assessment_type = request.form.get('assessment_type')
        subject = request.form.get('subject')

        if not all([grade, stream, term, assessment_type, subject]):
            return jsonify({
                'success': False,
                'message': 'Missing required parameters: grade, stream, term, assessment_type, subject'
            }), 400

        # Check permissions - only headteachers can delete from analytics
        role = get_role(session)
        is_headteacher = role == 'headteacher' or session.get('headteacher_universal_access')

        if not is_headteacher:
            return jsonify({
                'success': False,
                'message': 'Only headteachers can delete subject marks from analytics'
            }), 403

        # Import required models
        from ..models.academic import Mark, Student, Subject, Grade as GradeModel, Stream as StreamModel, Term as TermModel, AssessmentType
        from ..extensions import db

        # Extract stream letter from "Stream X" format if needed
        stream_letter = stream.replace("Stream ", "") if stream.startswith("Stream ") else stream

        # Get the objects
        grade_obj = GradeModel.query.filter_by(name=grade).first()
        if not grade_obj:
            return jsonify({
                'success': False,
                'message': f'Grade "{grade}" not found'
            }), 404

        stream_obj = StreamModel.query.filter(
            StreamModel.name == stream_letter,
            StreamModel.grade_id == grade_obj.id
        ).first()
        if not stream_obj:
            return jsonify({
                'success': False,
                'message': f'Stream "{stream}" not found in Grade {grade}'
            }), 404

        term_obj = TermModel.query.filter_by(name=term).first()
        if not term_obj:
            return jsonify({
                'success': False,
                'message': f'Term "{term}" not found'
            }), 404

        assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()
        if not assessment_type_obj:
            return jsonify({
                'success': False,
                'message': f'Assessment type "{assessment_type}" not found'
            }), 404

        subject_obj = Subject.query.filter_by(name=subject).first()
        if not subject_obj:
            return jsonify({
                'success': False,
                'message': f'Subject "{subject}" not found'
            }), 404

        # Delete marks for this specific combination
        marks_to_delete = Mark.query.join(Student).filter(
            Student.stream_id == stream_obj.id,
            Mark.term_id == term_obj.id,
            Mark.assessment_type_id == assessment_type_obj.id,
            Mark.subject_id == subject_obj.id
        ).all()

        deleted_count = len(marks_to_delete)

        if deleted_count == 0:
            return jsonify({
                'success': False,
                'message': f'No marks found for {subject} in Grade {grade} Stream {stream} ({term} - {assessment_type})'
            }), 404

        for mark in marks_to_delete:
            db.session.delete(mark)

        # Commit the changes
        db.session.commit()

        # Invalidate cache for this combination
        from ..services.cache_service import invalidate_cache
        invalidate_cache(grade, stream, term, assessment_type)

        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} marks for {subject} in Grade {grade} Stream {stream} ({term} - {assessment_type})',
            'deleted_count': deleted_count
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting subject marks: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error deleting subject marks: {str(e)}'
        }), 500


@analytics_api_bp.route('/filter_options')
@analytics_required
def get_filter_options():
    """Get available filter options for bulk delete."""
    try:
        # Check permissions - only headteachers can access this
        role = get_role(session)
        is_headteacher = role == 'headteacher' or session.get('headteacher_universal_access')

        if not is_headteacher:
            return jsonify({
                'success': False,
                'message': 'Only headteachers can access filter options'
            }), 403

        # Import required models
        from ..models.academic import Grade, Stream, Term, AssessmentType

        # Get all available options
        grades = Grade.query.all()
        streams = Stream.query.all()
        terms = Term.query.all()
        assessment_types = AssessmentType.query.filter_by(is_active=True).all()

        return jsonify({
            'success': True,
            'grades': [{'id': g.id, 'name': g.name} for g in grades],
            'streams': [{'id': s.id, 'name': s.name} for s in streams],
            'terms': [{'id': t.id, 'name': t.name} for t in terms],
            'assessment_types': [{'id': a.id, 'name': a.name} for a in assessment_types]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading filter options: {str(e)}'
        }), 500


@analytics_api_bp.route('/delete_preview')
@analytics_required
def get_delete_preview():
    """Get preview of reports that would be deleted."""
    try:
        # Check permissions - only headteachers can access this
        role = get_role(session)
        is_headteacher = role == 'headteacher' or session.get('headteacher_universal_access')

        if not is_headteacher:
            return jsonify({
                'success': False,
                'message': 'Only headteachers can preview deletions'
            }), 403

        # Get parameters
        section = request.args.get('section')
        scope = request.args.get('scope', 'all')
        grade_id = request.args.get('grade_id', type=int)
        stream_id = request.args.get('stream_id', type=int)
        term_id = request.args.get('term_id', type=int)
        assessment_type_id = request.args.get('assessment_type_id', type=int)

        # Import required models
        from ..models.academic import Mark, Student, Grade, Stream, Term, AssessmentType
        from sqlalchemy import func

        # Build base query
        query = Mark.query.join(Student)

        # Apply filters based on scope
        if scope == 'filtered':
            if grade_id:
                query = query.join(Stream).join(Grade).filter(Grade.id == grade_id)
            if stream_id:
                query = query.filter(Student.stream_id == stream_id)
            if term_id:
                query = query.filter(Mark.term_id == term_id)
            if assessment_type_id:
                query = query.filter(Mark.assessment_type_id == assessment_type_id)

        # Get counts
        marks_count = query.count()
        students_affected = query.with_entities(func.count(func.distinct(Student.id))).scalar()

        # Get preview items (sample of what will be deleted)
        preview_items = []
        if marks_count > 0:
            # Group by grade, stream, term, assessment for preview
            preview_query = query.join(Stream).join(Grade).join(Term).join(AssessmentType).with_entities(
                Grade.name.label('grade_name'),
                Stream.name.label('stream_name'),
                Term.name.label('term_name'),
                AssessmentType.name.label('assessment_name'),
                func.count(Mark.id).label('mark_count')
            ).group_by(Grade.name, Stream.name, Term.name, AssessmentType.name).limit(10)

            for item in preview_query.all():
                preview_items.append({
                    'description': f'{item.grade_name} Stream {item.stream_name} - {item.term_name} {item.assessment_name}',
                    'marks_count': item.mark_count
                })

        # Calculate reports count (unique combinations)
        reports_count = len(preview_items) if preview_items else 0

        return jsonify({
            'success': True,
            'reports_count': reports_count,
            'marks_count': marks_count,
            'students_affected': students_affected,
            'preview_items': preview_items
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading delete preview: {str(e)}'
        }), 500


@analytics_api_bp.route('/bulk_delete', methods=['POST'])
@analytics_required
def bulk_delete_reports():
    """Bulk delete reports based on filters."""
    try:
        # Check permissions - only headteachers can delete
        role = get_role(session)
        is_headteacher = role == 'headteacher' or session.get('headteacher_universal_access')

        if not is_headteacher:
            return jsonify({
                'success': False,
                'message': 'Only headteachers can delete reports'
            }), 403

        # Get parameters
        section = request.form.get('section')
        scope = request.form.get('scope', 'all')
        grade_id = request.form.get('grade_id', type=int)
        stream_id = request.form.get('stream_id', type=int)
        term_id = request.form.get('term_id', type=int)
        assessment_type_id = request.form.get('assessment_type_id', type=int)

        # Import required models
        from ..models.academic import Mark, Student, Grade, Stream, Term, AssessmentType
        from ..extensions import db

        # Build base query
        query = Mark.query.join(Student)

        # Apply filters based on scope
        if scope == 'filtered':
            if grade_id:
                query = query.join(Stream).join(Grade).filter(Grade.id == grade_id)
            if stream_id:
                query = query.filter(Student.stream_id == stream_id)
            if term_id:
                query = query.filter(Mark.term_id == term_id)
            if assessment_type_id:
                query = query.filter(Mark.assessment_type_id == assessment_type_id)

        # Get marks to delete
        marks_to_delete = query.all()
        deleted_count = len(marks_to_delete)

        if deleted_count == 0:
            return jsonify({
                'success': False,
                'message': 'No reports found matching the specified criteria'
            })

        # Delete marks
        for mark in marks_to_delete:
            db.session.delete(mark)

        # Commit the changes
        db.session.commit()

        # Invalidate relevant cache
        from ..services.cache_service import invalidate_analytics_cache
        invalidate_analytics_cache()

        # Build success message
        if section == 'top-performers':
            section_name = 'Top Performers'
        elif section == 'subject-performance':
            section_name = 'Subject Performance'
        elif section == 'top-subject-performers':
            section_name = 'Top Subject Performers'
        else:
            section_name = 'Analytics'

        scope_text = 'all' if scope == 'all' else 'filtered'

        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} marks from {section_name} ({scope_text} reports)',
            'deleted_count': deleted_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting reports: {str(e)}'
        }), 500


@analytics_api_bp.route('/top_subject_performers')
@analytics_required
def get_top_subject_performers():
    """Get top 3 performers per subject per grade per stream."""
    try:
        current_app.logger.info("Starting get_top_subject_performers request")
        # Get query parameters
        grade_id = request.args.get('grade_id', type=int)
        stream_id = request.args.get('stream_id', type=int)
        term_id = request.args.get('term_id', type=int)
        assessment_type_id = request.args.get('assessment_type_id', type=int)

        # Apply role-based filtering
        role = get_role(session)
        teacher_id = session.get('teacher_id')

        # Import required models
        from ..models.academic import Mark, Student, Subject, Grade, Stream, Term, AssessmentType
        from ..models.assignment import TeacherSubjectAssignment
        from sqlalchemy import func, desc

        # Check if we have any marks data at all
        total_marks = Mark.query.count()
        total_students = Student.query.count()
        total_subjects = Subject.query.count()
        current_app.logger.info(f"Database stats - Marks: {total_marks}, Students: {total_students}, Subjects: {total_subjects}")

        if total_marks == 0:
            return jsonify({
                'success': True,
                'top_subject_performers': {},
                'total_combinations': 0,
                'message': f'No marks data available. Database has {total_students} students and {total_subjects} subjects but no marks recorded.'
            })

        # Build base query with proper joins - step by step for better error handling
        try:
            # Start with marks and add joins one by one
            base_query = Mark.query
            current_app.logger.info("Starting with Mark query")

            # Join with Student
            base_query = base_query.join(Student, Mark.student_id == Student.id)
            current_app.logger.info("Joined with Student")

            # Join with Subject
            base_query = base_query.join(Subject, Mark.subject_id == Subject.id)
            current_app.logger.info("Joined with Subject")

            # Join with Stream through Student
            base_query = base_query.join(Stream, Student.stream_id == Stream.id)
            current_app.logger.info("Joined with Stream")

            # Join with Grade through Stream
            base_query = base_query.join(Grade, Stream.grade_id == Grade.id)
            current_app.logger.info("Joined with Grade")

            # Join with Term
            base_query = base_query.join(Term, Mark.term_id == Term.id)
            current_app.logger.info("Joined with Term")

            # Join with AssessmentType
            base_query = base_query.join(AssessmentType, Mark.assessment_type_id == AssessmentType.id)
            current_app.logger.info("All joins completed successfully")

        except Exception as join_error:
            current_app.logger.error(f"Error in joins: {str(join_error)}")
            import traceback
            current_app.logger.error(f"Join traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'message': f'Database join error: {str(join_error)}'
            }), 500

        # Apply role-based filtering
        if role == 'classteacher' and not session.get('headteacher_universal_access'):
            # Filter to only subjects/classes this teacher is assigned to
            assigned_subjects = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher_id).all()
            if assigned_subjects:
                subject_ids = [a.subject_id for a in assigned_subjects]
                grade_ids = [a.grade_id for a in assigned_subjects]
                stream_ids = [a.stream_id for a in assigned_subjects if a.stream_id]

                base_query = base_query.filter(Subject.id.in_(subject_ids))
                base_query = base_query.filter(Grade.id.in_(grade_ids))
                if stream_ids:
                    base_query = base_query.filter(Stream.id.in_(stream_ids))

        # Apply filters
        if grade_id:
            base_query = base_query.filter(Grade.id == grade_id)
        if stream_id:
            base_query = base_query.filter(Stream.id == stream_id)
        if term_id:
            base_query = base_query.filter(Term.id == term_id)
        if assessment_type_id:
            base_query = base_query.filter(AssessmentType.id == assessment_type_id)

        # Get all combinations of grade, stream, subject
        try:
            combinations_query = base_query.with_entities(
                Grade.id.label('grade_id'),
                Grade.name.label('grade_name'),
                Stream.id.label('stream_id'),
                Stream.name.label('stream_name'),
                Subject.id.label('subject_id'),
                Subject.name.label('subject_name')
            ).distinct()

            combinations = combinations_query.all()
            current_app.logger.info(f"Found {len(combinations)} combinations")

        except Exception as combinations_error:
            current_app.logger.error(f"Error getting combinations: {str(combinations_error)}")
            import traceback
            current_app.logger.error(f"Combinations traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'message': f'Error getting data combinations: {str(combinations_error)}'
            }), 500

        result = {}

        if not combinations:
            current_app.logger.info("No combinations found, returning empty result")
            return jsonify({
                'success': True,
                'top_subject_performers': {},
                'total_combinations': 0,
                'message': 'No data available for the selected criteria'
            })

        for combo in combinations:
            grade_key = f"Grade {combo.grade_name}"
            stream_key = f"Stream {combo.stream_name}"
            subject_key = combo.subject_name

            if grade_key not in result:
                result[grade_key] = {}
            if stream_key not in result[grade_key]:
                result[grade_key][stream_key] = {}

            # Get top 3 performers for this combination
            top_performers_query = base_query.filter(
                Grade.id == combo.grade_id,
                Stream.id == combo.stream_id,
                Subject.id == combo.subject_id
            ).with_entities(
                Student.id.label('student_id'),
                Student.name.label('student_name'),
                Student.admission_number.label('admission_number'),
                Mark.mark.label('marks'),  # Fixed: use 'mark' instead of 'marks'
                Mark.total_marks.label('total_marks'),
                func.round((Mark.mark * 100.0 / Mark.total_marks), 2).label('percentage')  # Fixed: use 'mark' instead of 'marks'
            ).order_by(desc('percentage')).limit(3)

            top_performers = []
            for performer in top_performers_query.all():
                # Calculate grade letter based on percentage
                percentage = float(performer.percentage)
                grade_letter = calculate_grade_letter(percentage)

                top_performers.append({
                    'student_id': performer.student_id,
                    'student_name': performer.student_name,
                    'admission_number': performer.admission_number,
                    'marks': performer.marks,
                    'total_marks': performer.total_marks,
                    'percentage': percentage,
                    'grade_letter': grade_letter,
                    'position': len(top_performers) + 1
                })

            result[grade_key][stream_key][subject_key] = {
                'top_performers': top_performers,
                'total_students': base_query.filter(
                    Grade.id == combo.grade_id,
                    Stream.id == combo.stream_id,
                    Subject.id == combo.subject_id
                ).with_entities(func.count(func.distinct(Student.id))).scalar()
            }

        return jsonify({
            'success': True,
            'top_subject_performers': result,
            'total_combinations': len(combinations)
        })

    except Exception as e:
        current_app.logger.error(f"Error in get_top_subject_performers: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'Error loading top subject performers: {str(e)}'
        }), 500


def calculate_grade_letter(percentage):
    """Calculate grade letter based on percentage."""
    if percentage >= 90:
        return 'EE1'
    elif percentage >= 80:
        return 'EE2'
    elif percentage >= 70:
        return 'ME1'
    elif percentage >= 60:
        return 'ME2'
    elif percentage >= 50:
        return 'AE1'
    elif percentage >= 40:
        return 'AE2'
    elif percentage >= 30:
        return 'BE1'
    else:
        return 'BE2'


@analytics_api_bp.route('/database_status')
@analytics_required
def get_database_status():
    """Get database status for debugging."""
    try:
        # Import required models
        from ..models.academic import Mark, Student, Subject, Grade, Stream, Term, AssessmentType

        # Get counts
        marks_count = Mark.query.count()
        students_count = Student.query.count()
        subjects_count = Subject.query.count()
        grades_count = Grade.query.count()
        streams_count = Stream.query.count()
        terms_count = Term.query.count()
        assessment_types_count = AssessmentType.query.count()

        # Get sample data
        sample_marks = Mark.query.limit(5).all()
        sample_students = Student.query.limit(5).all()

        return jsonify({
            'success': True,
            'database_status': {
                'marks_count': marks_count,
                'students_count': students_count,
                'subjects_count': subjects_count,
                'grades_count': grades_count,
                'streams_count': streams_count,
                'terms_count': terms_count,
                'assessment_types_count': assessment_types_count,
                'sample_marks': [
                    {
                        'id': mark.id,
                        'student_id': mark.student_id,
                        'subject_id': mark.subject_id,
                        'marks': mark.mark,  # Fixed: use 'mark' instead of 'marks'
                        'total_marks': mark.total_marks
                    } for mark in sample_marks
                ],
                'sample_students': [
                    {
                        'id': student.id,
                        'name': student.name,
                        'stream_id': student.stream_id
                    } for student in sample_students
                ]
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting database status: {str(e)}'
        }), 500


@analytics_api_bp.route('/test_simple_data')
@analytics_required
def test_simple_data():
    """Test endpoint to get simple data without complex joins."""
    try:
        # Import required models
        from ..models.academic import Mark, Student, Subject, Grade, Stream, Term, AssessmentType

        # Get simple counts
        marks_count = Mark.query.count()
        students_count = Student.query.count()

        # Get a few sample records
        sample_marks = Mark.query.limit(3).all()
        sample_students = Student.query.limit(3).all()

        # Try simple joins one by one
        marks_with_students = []
        for mark in sample_marks:
            try:
                student = Student.query.get(mark.student_id)
                subject = Subject.query.get(mark.subject_id)
                term = Term.query.get(mark.term_id)
                assessment = AssessmentType.query.get(mark.assessment_type_id)

                mark_data = {
                    'mark_id': mark.id,
                    'marks': mark.mark,  # Fixed: use 'mark' instead of 'marks'
                    'total_marks': mark.total_marks,
                    'student_name': student.name if student else 'Unknown',
                    'subject_name': subject.name if subject else 'Unknown',
                    'term_name': term.name if term else 'Unknown',
                    'assessment_name': assessment.name if assessment else 'Unknown'
                }

                if student and student.stream_id:
                    stream = Stream.query.get(student.stream_id)
                    if stream:
                        mark_data['stream_name'] = stream.name
                        grade = Grade.query.get(stream.grade_id)
                        if grade:
                            mark_data['grade_name'] = grade.name

                marks_with_students.append(mark_data)

            except Exception as e:
                current_app.logger.error(f"Error processing mark {mark.id}: {str(e)}")

        return jsonify({
            'success': True,
            'test_data': {
                'marks_count': marks_count,
                'students_count': students_count,
                'sample_marks_with_details': marks_with_students
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error in test_simple_data: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'Error in test: {str(e)}'
        }), 500


@analytics_api_bp.route('/export')
@analytics_required
def export_analytics_data():
    """Export analytics data in various formats."""
    try:
        # Check permissions - only headteachers can export
        role = get_role(session)
        is_headteacher = role == 'headteacher' or session.get('headteacher_universal_access')

        if not is_headteacher:
            return jsonify({
                'success': False,
                'message': 'Only headteachers can export analytics data'
            }), 403

        # Get parameters
        section = request.args.get('section', 'all')
        format_type = request.args.get('format', 'excel')
        grade_id = request.args.get('grade_id', type=int)
        stream_id = request.args.get('stream_id', type=int)
        term_id = request.args.get('term_id', type=int)
        assessment_type_id = request.args.get('assessment_type_id', type=int)

        # Import services
        from ..services.analytics_export_service import AnalyticsExportService
        from ..services.academic_analytics_service import AcademicAnalyticsService
        from flask import make_response

        # Get analytics data based on section
        filters = {
            'grade_id': grade_id,
            'stream_id': stream_id,
            'term_id': term_id,
            'assessment_type_id': assessment_type_id
        }

        if section == 'all' or section == 'top-performers':
            # Get top performers data
            analytics_data = {
                'top_performers': AcademicAnalyticsService.get_enhanced_top_performers(
                    grade_id=grade_id,
                    stream_id=stream_id,
                    term_id=term_id,
                    assessment_type_id=assessment_type_id
                ).get('enhanced_top_performers', []),
                'summary': {
                    'total_students_analyzed': 0,
                    'total_subjects_analyzed': 0,
                    'has_sufficient_data': True
                }
            }
        elif section == 'subject-performance':
            # Get subject performance data
            analytics_data = {
                'subject_analytics': [],  # Would need to implement this
                'summary': {
                    'total_students_analyzed': 0,
                    'total_subjects_analyzed': 0,
                    'has_sufficient_data': True
                }
            }
        elif section == 'top-subject-performers':
            # Get top subject performers data
            top_performers_response = get_top_subject_performers()
            if hasattr(top_performers_response, 'get_json'):
                top_performers_data = top_performers_response.get_json()
                analytics_data = {
                    'top_subject_performers': top_performers_data.get('top_subject_performers', {}),
                    'summary': {
                        'total_students_analyzed': 0,
                        'total_subjects_analyzed': 0,
                        'has_sufficient_data': True
                    }
                }
            else:
                analytics_data = {'summary': {'has_sufficient_data': False}}
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid section specified'
            }), 400

        # Generate export based on format
        if format_type == 'excel':
            file_data = AnalyticsExportService.export_analytics_excel(analytics_data, filters)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'{section}_analytics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        elif format_type == 'pdf':
            file_data = AnalyticsExportService.export_analytics_pdf(analytics_data, filters)
            mimetype = 'application/pdf'
            filename = f'{section}_analytics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        elif format_type == 'word':
            file_data = AnalyticsExportService.export_analytics_word(analytics_data, filters)
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            filename = f'{section}_analytics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx'
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid format specified'
            }), 400

        # Create response
        response = make_response(file_data)
        response.headers['Content-Type'] = mimetype
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error exporting analytics data: {str(e)}'
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


@analytics_api_bp.route('/class-stream-performance')
@analytics_required
def get_class_stream_performance():
    """Get performance analytics by class and stream."""
    try:
        # Get query parameters
        term_id = request.args.get('term_id', type=int)
        assessment_type_id = request.args.get('assessment_type_id', type=int)

        # Check permissions
        role = get_role(session)
        if role not in ['headteacher', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Insufficient permissions'
            }), 403

        # Get class/stream performance data
        result = AcademicAnalyticsService.get_class_stream_performance(
            term_id=term_id,
            assessment_type_id=assessment_type_id
        )

        return jsonify({
            'success': True,
            'class_stream_performance': result.get('class_stream_performance', []),
            'total_classes_analyzed': result.get('total_classes_analyzed', 0),
            'best_performing_class': result.get('best_performing_class'),
            'lowest_performing_class': result.get('lowest_performing_class')
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting class-stream performance: {str(e)}'
        }), 500


@analytics_api_bp.route('/enhanced-top-performers')
@analytics_required
def get_enhanced_top_performers():
    """Get enhanced top performers with detailed marks breakdown."""
    try:
        # Get query parameters
        grade_id = request.args.get('grade_id', type=int)
        stream_id = request.args.get('stream_id', type=int)
        term_id = request.args.get('term_id', type=int)
        assessment_type_id = request.args.get('assessment_type_id', type=int)
        limit = request.args.get('limit', default=10, type=int)

        # Apply role-based filtering
        role = get_role(session)
        teacher_id = session.get('teacher_id')

        if role == 'classteacher':
            # Classteachers can only see analytics for their assigned classes
            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, 'classteacher')

            if 'error' in assignment_summary:
                return jsonify({
                    'success': True,
                    'enhanced_top_performers': {},
                    'total_grades_analyzed': 0,
                    'message': assignment_summary['error']
                })

            assigned_classes = assignment_summary.get('class_teacher_assignments', [])
            if not assigned_classes:
                return jsonify({
                    'success': True,
                    'enhanced_top_performers': {},
                    'total_grades_analyzed': 0,
                    'message': 'No assigned classes found'
                })

            # If no specific grade/stream provided, use first assigned class
            if not grade_id and not stream_id and assigned_classes:
                first_class = assigned_classes[0]
                grade_id = first_class.get('grade_id')
                stream_id = first_class.get('stream_id')

        # Get enhanced top performers data
        result = AcademicAnalyticsService.get_enhanced_top_performers(
            grade_id=grade_id,
            stream_id=stream_id,
            term_id=term_id,
            assessment_type_id=assessment_type_id,
            limit=limit
        )

        return jsonify({
            'success': True,
            'enhanced_top_performers': result.get('enhanced_top_performers', {}),
            'total_grades_analyzed': result.get('total_grades_analyzed', 0)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting enhanced top performers: {str(e)}'
        }), 500


@analytics_api_bp.route('/streams')
@analytics_required
def get_streams():
    """Get available streams based on grade selection and user permissions."""
    try:
        grade_id = request.args.get('grade_id', type=int)
        role = get_role(session)
        teacher_id = session.get('teacher_id')

        if role == 'headteacher':
            # Headteachers can see all streams for the selected grade
            if grade_id:
                streams = Stream.query.filter_by(grade_id=grade_id).all()
            else:
                streams = Stream.query.all()
        elif role == 'classteacher':
            # Classteachers can only see their assigned streams
            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, 'classteacher')

            if 'error' not in assignment_summary:
                assigned_classes = assignment_summary.get('class_teacher_assignments', [])

                # Filter by grade if provided
                if grade_id:
                    stream_ids = set(assignment.get('stream_id') for assignment in assigned_classes
                                   if assignment.get('grade_id') == grade_id and assignment.get('stream_id'))
                else:
                    stream_ids = set(assignment.get('stream_id') for assignment in assigned_classes
                                   if assignment.get('stream_id'))

                if stream_ids:
                    streams = Stream.query.filter(Stream.id.in_(stream_ids)).all()
                else:
                    streams = []
            else:
                streams = []
        else:
            streams = []

        streams_data = [{
            'id': stream.id,
            'name': stream.name,
            'grade_id': stream.grade_id
        } for stream in streams]

        return jsonify({
            'success': True,
            'streams': streams_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting streams: {str(e)}'
        }), 500


@analytics_api_bp.route('/export/<format_type>')
@analytics_required
def export_analytics(format_type):
    """Export analytics data in specified format (pdf, word, excel)."""
    try:
        from flask import make_response
        from ..services.analytics_export_service import AnalyticsExportService

        # Validate format
        if format_type not in ['pdf', 'word', 'excel']:
            return jsonify({
                'success': False,
                'message': 'Invalid export format. Supported formats: pdf, word, excel'
            }), 400

        # Get query parameters for filtering
        grade_id = request.args.get('grade_id', type=int)
        stream_id = request.args.get('stream_id', type=int)
        term_id = request.args.get('term_id', type=int)
        assessment_type_id = request.args.get('assessment_type_id', type=int)

        # Apply role-based filtering
        role = get_role(session)
        teacher_id = session.get('teacher_id')

        if role == 'classteacher':
            # Classteachers can only export analytics for their assigned classes
            assignment_summary = RoleBasedDataService.get_teacher_assignments_summary(teacher_id, 'classteacher')

            if 'error' in assignment_summary:
                return jsonify({
                    'success': False,
                    'message': 'No class assignments found for export'
                }), 403

            assigned_classes = assignment_summary.get('class_teacher_assignments', [])
            if not assigned_classes:
                return jsonify({
                    'success': False,
                    'message': 'No assigned classes found for export'
                }), 403

            # If no specific grade/stream provided, use first assigned class
            if not grade_id and not stream_id and assigned_classes:
                first_class = assigned_classes[0]
                grade_id = first_class.get('grade_id')
                stream_id = first_class.get('stream_id')

        # Get comprehensive analytics data
        analytics_data = AcademicAnalyticsService.get_comprehensive_analytics(
            grade_id=grade_id,
            stream_id=stream_id,
            term_id=term_id,
            assessment_type_id=assessment_type_id,
            top_performers_limit=20  # More data for export
        )

        # Prepare filter context for the export
        filters = {}
        if grade_id:
            from ..models import Grade
            grade = Grade.query.get(grade_id)
            filters['grade_id'] = grade_id
            filters['grade_name'] = grade.name if grade else f"Grade {grade_id}"

        if stream_id:
            from ..models import Stream
            stream = Stream.query.get(stream_id)
            filters['stream_id'] = stream_id
            filters['stream_name'] = stream.name if stream else f"Stream {stream_id}"

        if term_id:
            from ..models import Term
            term = Term.query.get(term_id)
            filters['term_id'] = term_id
            filters['term_name'] = term.name if term else f"Term {term_id}"

        if assessment_type_id:
            from ..models import AssessmentType
            assessment_type = AssessmentType.query.get(assessment_type_id)
            filters['assessment_type_id'] = assessment_type_id
            filters['assessment_type_name'] = assessment_type.name if assessment_type else f"Assessment {assessment_type_id}"

        # Generate export based on format
        if format_type == 'pdf':
            file_data = AnalyticsExportService.export_analytics_pdf(analytics_data, filters)
            mimetype = 'application/pdf'
            filename = f'analytics_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'

        elif format_type == 'word':
            file_data = AnalyticsExportService.export_analytics_word(analytics_data, filters)
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            filename = f'analytics_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx'

        elif format_type == 'excel':
            file_data = AnalyticsExportService.export_analytics_excel(analytics_data, filters)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'analytics_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

        # Create response
        response = make_response(file_data)
        response.headers['Content-Type'] = mimetype
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Length'] = len(file_data)

        return response

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error exporting analytics: {str(e)}'
        }), 500
