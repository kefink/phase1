"""
Headteacher Universal Access Views - Provides headteacher with access to all classteacher functions
across all grades and streams with intelligent class structure detection.
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from ..services.headteacher_universal_service import HeadteacherUniversalService
from ..services.class_structure_service import ClassStructureService
from ..services import is_authenticated, get_role
from functools import wraps

# Create blueprint
universal_bp = Blueprint('universal', __name__, url_prefix='/universal')

def headteacher_required(f):
    """Decorator to require headteacher authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session):
            return redirect(url_for('auth.admin_login'))
        
        role = get_role(session)
        if role != 'headteacher':
            flash('Access denied. This feature is only available to headteachers.', 'error')
            return redirect(url_for('auth.admin_login'))
        
        return f(*args, **kwargs)
    return decorated_function



@universal_bp.route('/dashboard')
@headteacher_required
def dashboard():
    """Universal dashboard for headteacher access to all class functions."""
    try:
        # Get comprehensive dashboard data
        dashboard_data = HeadteacherUniversalService.get_universal_dashboard_data()

        return render_template(
            'headteacher_universal.html',
            dashboard_data=dashboard_data,
            page_title="Universal Class Management"
        )

    except Exception as e:
        # More detailed error handling
        import traceback
        error_details = traceback.format_exc()
        flash(f'Error loading universal dashboard: {str(e)}', 'error')
        print(f"Universal dashboard error: {error_details}")

        # Fallback with basic data
        dashboard_data = {
            'class_statistics': {
                'total_grades': 9,
                'total_classes': 27,
                'total_students': 0,
                'structure_type': 'mixed_structure'
            },
            'school_structure': {
                'grades': [],
                'total_classes': 27,
                'uses_streams': True,
                'mixed_structure': True
            },
            'recent_activity': [],
            'performance_overview': {},
            'teacher_assignments': []
        }

        return render_template(
            'headteacher_universal.html',
            dashboard_data=dashboard_data,
            page_title="Universal Class Management"
        )

@universal_bp.route('/api/school_structure')
@headteacher_required
def get_school_structure():
    """API endpoint to get school structure data."""
    try:
        structure = ClassStructureService.get_school_structure()
        return jsonify({'success': True, 'structure': structure})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@universal_bp.route('/api/class_selection')
@headteacher_required
def get_class_selection():
    """API endpoint to get all classes formatted for selection."""
    try:
        classes = ClassStructureService.get_all_classes_for_selection()
        return jsonify({'success': True, 'classes': classes})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@universal_bp.route('/api/class_data/<path:class_identifier>')
@headteacher_required
def get_class_data(class_identifier):
    """API endpoint to get comprehensive data for a specific class."""
    try:
        # Parse class identifier
        grade_name, stream_name = ClassStructureService.parse_class_identifier(class_identifier)
        
        # Get class data
        class_data = HeadteacherUniversalService.get_class_specific_data(grade_name, stream_name)
        
        if 'error' in class_data:
            return jsonify({'success': False, 'message': class_data['error']})
        
        return jsonify({'success': True, 'class_data': class_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@universal_bp.route('/class_manager/<path:class_identifier>')
@headteacher_required
def class_manager(class_identifier):
    """Universal class manager for specific class."""
    try:
        # Parse class identifier
        grade_name, stream_name = ClassStructureService.parse_class_identifier(class_identifier)
        
        # Get class data
        class_data = HeadteacherUniversalService.get_class_specific_data(grade_name, stream_name)
        
        if 'error' in class_data:
            flash(f'Error: {class_data["error"]}', 'error')
            return redirect(url_for('universal.dashboard'))
        
        # Get school structure for navigation
        structure = ClassStructureService.get_school_structure()
        
        return render_template(
            'universal_class_manager.html',
            class_data=class_data,
            school_structure=structure,
            class_identifier=class_identifier,
            page_title=f"Managing {class_data['class_name']}"
        )
        
    except Exception as e:
        flash(f'Error loading class manager: {str(e)}', 'error')
        return redirect(url_for('universal.dashboard'))

@universal_bp.route('/api/switch_class', methods=['POST'])
@headteacher_required
def switch_class():
    """API endpoint to switch to a different class context."""
    try:
        data = request.get_json()
        class_identifier = data.get('class_identifier')
        
        if not class_identifier:
            return jsonify({'success': False, 'message': 'Class identifier required'})
        
        # Validate class exists
        grade_name, stream_name = ClassStructureService.parse_class_identifier(class_identifier)
        class_data = HeadteacherUniversalService.get_class_specific_data(grade_name, stream_name)
        
        if 'error' in class_data:
            return jsonify({'success': False, 'message': class_data['error']})
        
        # Store current class context in session
        session['universal_class_context'] = {
            'class_identifier': class_identifier,
            'grade_name': grade_name,
            'stream_name': stream_name,
            'class_name': class_data['class_name']
        }
        
        return jsonify({
            'success': True,
            'message': f'Switched to {class_data["class_name"]}',
            'redirect_url': url_for('universal.class_manager', class_identifier=class_identifier)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@universal_bp.route('/api/class_statistics')
@headteacher_required
def get_class_statistics():
    """API endpoint to get comprehensive class statistics."""
    try:
        stats = ClassStructureService.get_class_statistics()
        return jsonify({'success': True, 'statistics': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@universal_bp.route('/api/performance_overview')
@headteacher_required
def get_performance_overview():
    """API endpoint to get performance overview across all classes."""
    try:
        dashboard_data = HeadteacherUniversalService.get_universal_dashboard_data()
        performance = dashboard_data.get('performance_overview', {})
        return jsonify({'success': True, 'performance': performance})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@universal_bp.route('/api/recent_activity')
@headteacher_required
def get_recent_activity():
    """API endpoint to get recent activity across all classes."""
    try:
        dashboard_data = HeadteacherUniversalService.get_universal_dashboard_data()
        activity = dashboard_data.get('recent_activity', [])
        return jsonify({'success': True, 'activity': activity})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================================================
# COMPREHENSIVE PROXY ROUTES FOR ALL CLASSTEACHER FUNCTIONS
# ============================================================================

# STUDENT MANAGEMENT PROXIES
@universal_bp.route('/proxy/manage_students')
@headteacher_required
def proxy_manage_students():
    """Proxy to student management."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.manage_students'))

@universal_bp.route('/proxy/download_student_template')
@headteacher_required
def proxy_download_student_template():
    """Proxy to download student template."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.download_student_template'))

@universal_bp.route('/proxy/download_class_list')
@headteacher_required
def proxy_download_class_list():
    """Proxy to download class list."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.download_class_list'))

# SUBJECT MANAGEMENT PROXIES
@universal_bp.route('/proxy/manage_subjects')
@headteacher_required
def proxy_manage_subjects():
    """Proxy to subject management."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.manage_subjects'))

@universal_bp.route('/proxy/download_subject_template')
@headteacher_required
def proxy_download_subject_template():
    """Proxy to download subject template."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.download_subject_template'))

@universal_bp.route('/proxy/export_subjects')
@headteacher_required
def proxy_export_subjects():
    """Proxy to export subjects."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.export_subjects'))

# TEACHER MANAGEMENT PROXIES
@universal_bp.route('/proxy/teacher_management_hub')
@headteacher_required
def proxy_teacher_management_hub():
    """Proxy to teacher management hub."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.teacher_management_hub'))

@universal_bp.route('/proxy/manage_teachers')
@headteacher_required
def proxy_manage_teachers():
    """Proxy to teacher management."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.manage_teachers'))

@universal_bp.route('/proxy/assign_subjects')
@headteacher_required
def proxy_assign_subjects():
    """Proxy to subject assignment."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.assign_subjects'))

@universal_bp.route('/proxy/advanced_assignments')
@headteacher_required
def proxy_advanced_assignments():
    """Proxy to advanced assignments."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.advanced_assignments'))

# GRADE & STREAM MANAGEMENT PROXIES
@universal_bp.route('/proxy/manage_grades_streams')
@headteacher_required
def proxy_manage_grades_streams():
    """Proxy to grades and streams management."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.manage_grades_streams'))

# TERMS & ASSESSMENT MANAGEMENT PROXIES
@universal_bp.route('/proxy/manage_terms_assessments')
@headteacher_required
def proxy_manage_terms_assessments():
    """Proxy to terms and assessments management."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.manage_terms_assessments'))

# MARKS MANAGEMENT PROXIES
@universal_bp.route('/proxy/classteacher_dashboard')
@headteacher_required
def proxy_classteacher_dashboard():
    """Proxy to classteacher dashboard for marks upload."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.dashboard'))

@universal_bp.route('/proxy/download_marks_template')
@headteacher_required
def proxy_download_marks_template():
    """Proxy to download marks template."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.download_marks_template'))

@universal_bp.route('/proxy/collaborative_marks_dashboard')
@headteacher_required
def proxy_collaborative_marks_dashboard():
    """Proxy to collaborative marks dashboard."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.collaborative_marks_dashboard'))

# REPORT MANAGEMENT PROXIES
@universal_bp.route('/proxy/view_all_reports')
@headteacher_required
def proxy_view_all_reports():
    """Proxy to view all reports."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.view_all_reports'))

@universal_bp.route('/proxy/grade_reports_dashboard')
@headteacher_required
def proxy_grade_reports_dashboard():
    """Proxy to grade reports dashboard."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.grade_reports_dashboard'))

# ASSIGNMENT MANAGEMENT PROXIES
@universal_bp.route('/proxy/manage_teacher_assignments')
@headteacher_required
def proxy_manage_teacher_assignments():
    """Proxy to teacher assignments management."""
    session['headteacher_universal_access'] = True
    return redirect(url_for('classteacher.manage_teacher_assignments'))

# CLASS-SPECIFIC PROXIES
@universal_bp.route('/proxy/students/<path:class_identifier>')
@headteacher_required
def proxy_students(class_identifier):
    """Proxy to student management for specific class."""
    try:
        # Set class context and redirect to classteacher student management
        grade_name, stream_name = ClassStructureService.parse_class_identifier(class_identifier)

        # Store context for the proxied request
        session['proxy_class_context'] = {
            'grade_name': grade_name,
            'stream_name': stream_name,
            'is_headteacher_proxy': True
        }
        session['headteacher_universal_access'] = True

        # Redirect to classteacher students view with context
        return redirect(url_for('classteacher.manage_students'))

    except Exception as e:
        flash(f'Error accessing student management: {str(e)}', 'error')
        return redirect(url_for('universal.dashboard'))

@universal_bp.route('/proxy/marks/<path:class_identifier>')
@headteacher_required
def proxy_marks(class_identifier):
    """Proxy to marks management for specific class."""
    try:
        # Set class context and redirect to classteacher marks management
        grade_name, stream_name = ClassStructureService.parse_class_identifier(class_identifier)

        # Store context for the proxied request
        session['proxy_class_context'] = {
            'grade_name': grade_name,
            'stream_name': stream_name,
            'is_headteacher_proxy': True
        }
        session['headteacher_universal_access'] = True

        # Redirect to classteacher marks view with context
        return redirect(url_for('classteacher.dashboard'))

    except Exception as e:
        flash(f'Error accessing marks management: {str(e)}', 'error')
        return redirect(url_for('universal.dashboard'))

@universal_bp.route('/proxy/reports/<path:class_identifier>')
@headteacher_required
def proxy_reports(class_identifier):
    """Proxy to reports generation for specific class."""
    try:
        # Set class context and redirect to classteacher reports
        grade_name, stream_name = ClassStructureService.parse_class_identifier(class_identifier)

        # Store context for the proxied request
        session['proxy_class_context'] = {
            'grade_name': grade_name,
            'stream_name': stream_name,
            'is_headteacher_proxy': True
        }
        session['headteacher_universal_access'] = True

        # Redirect to classteacher reports view with context
        return redirect(url_for('classteacher.view_all_reports'))

    except Exception as e:
        flash(f'Error accessing reports: {str(e)}', 'error')
        return redirect(url_for('universal.dashboard'))
