"""
Permission management views for headteacher delegation system.
Allows headteacher to grant/revoke classteacher permissions for specific classes/streams.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app, abort
from ..models import ClassTeacherPermission, Teacher, Grade, Stream
from ..services.permission_service import PermissionService
from ..security.authorization import require_roles
from ..services.enhanced_permission_service import EnhancedPermissionService
from ..services.enhanced_permission_management_service import EnhancedPermissionManagementService
from ..services import is_authenticated, get_role
from ..models.function_permission import DefaultFunctionPermissions
from ..extensions import csrf
from security_helpers import secure_endpoint, ValidationError, wants_json
from functools import wraps

# Create blueprint for permission management
permission_bp = Blueprint('permission', __name__, url_prefix='/permission')

# ---------------------------------------------------------------------------
# Feature Flags (temporary suspension of advanced permission features)
# Toggle values to True to re-enable. Using 404 for disabled features hides
# unfinished surfaces rather than exposing an authorization error.
# ---------------------------------------------------------------------------
FEATURE_FLAGS = {
    'CLASS_PERMISSION_MANAGEMENT': False,       # /permission/manage
    'FUNCTION_PERMISSION_MANAGEMENT': False,    # /permission/manage_functions
    'PERMISSION_REQUESTS_REVIEW': False         # /permission/requests
}

def feature_required(flag_key):
    """Decorator: abort with 404 if feature flag disabled."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not FEATURE_FLAGS.get(flag_key, False):
                try:
                    current_app.logger.info(f"Feature disabled (404): {flag_key}")
                except Exception:
                    pass
                abort(404)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def headteacher_required(f):
    """Decorator to require headteacher authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session) or get_role(session) != 'headteacher':
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@permission_bp.route('/manage')
@require_roles('headteacher')
@feature_required('CLASS_PERMISSION_MANAGEMENT')
def manage_permissions():
    """Enhanced permission management page for headteacher with pagination and filtering."""
    try:
        # Get pagination and filter parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        teacher_filter = request.args.get('teacher_filter', '', type=str)
        role_filter = request.args.get('role_filter', '', type=str)

        # Get comprehensive dashboard data with pagination
        dashboard_data = PermissionService.get_permission_dashboard_data(
            page=page,
            per_page=per_page,
            teacher_filter=teacher_filter,
            role_filter=role_filter
        )

        return render_template('enhanced_class_permission_management.html',
                             data=dashboard_data,
                             current_user=session.get('teacher_id'))

    except Exception as e:
        flash(f'Error loading permission management: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

def _validate_grant():
    teacher_id = request.form.get('teacher_id')
    perm = request.form.get('permission_code')
    missing = {}
    if not teacher_id:
        missing['teacher_id'] = 'required'
    if not perm:
        missing['permission_code'] = 'required'
    if missing:
        raise ValidationError('Missing required fields', missing)
    if not str(teacher_id).isdigit():
        raise ValidationError('teacher_id must be numeric')
    return {'teacher_id': int(teacher_id), 'permission_code': perm}

@permission_bp.route('/grant', methods=['POST'])
@secure_endpoint(roles=['admin','headteacher'], rate=(30,60), validator=_validate_grant, audit_event='permission.grant')
def grant_permission(_validated):
    data = _validated
    # Simulated persistence layer action
    return jsonify({'status':'ok','granted': data}), 200

def _validate_revoke():
    data = request.get_json(silent=True) or {}
    teacher_id = data.get('teacher_id')
    grade_name = data.get('grade_name')
    stream_name = data.get('stream_name')  # optional
    missing = {}
    if not teacher_id: missing['teacher_id'] = 'required'
    if not grade_name: missing['grade_name'] = 'required'
    if missing:
        raise ValidationError('Missing required fields', missing)
    return {'teacher_id': teacher_id, 'grade_name': grade_name, 'stream_name': stream_name}

@permission_bp.route('/revoke', methods=['POST'])
@secure_endpoint(roles=['headteacher','admin'], rate=(30,60), validator=_validate_revoke, audit_event='permission.revoke')
def revoke_permission(_validated):
    v = _validated
    success, message = PermissionService.revoke_permission(
        teacher_id=v['teacher_id'],
        grade_name=v['grade_name'],
        stream_name=v['stream_name']
    )
    return jsonify({'success': success, 'message': message})

@permission_bp.route('/teacher/<int:teacher_id>/permissions')
@require_roles('headteacher')
def get_teacher_permissions(teacher_id):
    """Get all permissions for a specific teacher."""
    try:
        permissions = PermissionService.get_teacher_assigned_classes(teacher_id)
        return jsonify({'success': True, 'permissions': permissions})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting permissions: {str(e)}'})

# Removed duplicate - using the enhanced version below

@permission_bp.route('/bulk_grant', methods=['POST'])
@require_roles('headteacher')
def bulk_grant_permissions():
    """Grant multiple permissions at once."""
    try:
        data = request.get_json()
        assignments = data.get('assignments', [])  # List of {teacher_id, grade_name, stream_name}
        notes = data.get('notes', '')
        
        granted_by_id = session.get('teacher_id')
        results = []
        
        for assignment in assignments:
            success, message = PermissionService.grant_permission(
                teacher_id=assignment.get('teacher_id'),
                grade_name=assignment.get('grade_name'),
                stream_name=assignment.get('stream_name'),
                granted_by_id=granted_by_id,
                notes=notes
            )
            
            results.append({
                'assignment': assignment,
                'success': success,
                'message': message
            })
        
        # Count successes
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        return jsonify({
            'success': True,
            'message': f'Granted {successful}/{total} permissions successfully',
            'results': results
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error in bulk grant: {str(e)}'})

@permission_bp.route('/permission_status/<int:teacher_id>')
def get_permission_status(teacher_id):
    """Get permission status for a teacher (accessible by the teacher themselves)."""
    try:
        # Allow teachers to check their own permissions
        current_teacher_id = session.get('teacher_id')
        current_role = get_role(session)
        
        if current_role != 'headteacher' and current_teacher_id != teacher_id:
            return jsonify({'success': False, 'message': 'Unauthorized'})
        
        permissions = PermissionService.get_teacher_assigned_classes(teacher_id)
        
        return jsonify({
            'success': True,
            'permissions': permissions,
            'has_permissions': len(permissions) > 0
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting status: {str(e)}'})

# API endpoint for classteacher dashboard to show permission status
@permission_bp.route('/my_permissions_api')
def my_permissions_api():
    """Get current user's permissions for display in classteacher dashboard (JSON API)."""
    try:
        if not is_authenticated(session):
            return jsonify({'success': False, 'message': 'Not authenticated'})

        teacher_id = session.get('teacher_id')
        role = get_role(session)

        if role == 'headteacher':
            # Headteacher has access to everything
            return jsonify({
                'success': True,
                'permissions': [],
                'has_permissions': True,
                'is_headteacher': True,
                'message': 'Full administrative access'
            })

        elif role == 'classteacher':
            permissions = PermissionService.get_teacher_assigned_classes(teacher_id)

            return jsonify({
                'success': True,
                'permissions': permissions,
                'has_permissions': len(permissions) > 0,
                'is_headteacher': False,
                'message': f'Access to {len(permissions)} class(es)' if permissions else 'No class permissions assigned'
            })

        else:
            return jsonify({
                'success': True,
                'permissions': [],
                'has_permissions': False,
                'is_headteacher': False,
                'message': 'No administrative permissions'
            })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting permissions: {str(e)}'})

@permission_bp.route('/request', methods=['POST'])
def request_permission():
    """Submit a permission request from a classteacher."""
    try:
        if not is_authenticated(session):
            return jsonify({'success': False, 'message': 'Not authenticated'})

        teacher_id = session.get('teacher_id')
        role = get_role(session)

        # Only classteachers can request permissions
        if role != 'classteacher':
            return jsonify({'success': False, 'message': 'Only classteachers can request permissions'})

        data = request.get_json()
        grade_name = data.get('grade_name')
        stream_name = data.get('stream_name')
        reason = data.get('reason', '')

        if not grade_name:
            return jsonify({'success': False, 'message': 'Grade is required'})

        # Submit the request
        success, message = PermissionService.submit_permission_request(
            teacher_id=teacher_id,
            grade_name=grade_name,
            stream_name=stream_name,
            reason=reason
        )

        return jsonify({'success': success, 'message': message})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error submitting request: {str(e)}'})

@permission_bp.route('/requests')
@require_roles('headteacher')
@feature_required('PERMISSION_REQUESTS_REVIEW')
def get_pending_requests():
    """Get all pending permission requests for headteacher review."""
    try:
        requests = PermissionService.get_pending_requests()
        return jsonify({'success': True, 'requests': requests})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting requests: {str(e)}'})

@permission_bp.route('/process_request', methods=['POST'])
@require_roles('headteacher')
def process_permission_request():
    """Approve or deny a permission request."""
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        action = data.get('action')  # 'approve' or 'deny'
        admin_notes = data.get('admin_notes', '')

        if not request_id or action not in ['approve', 'deny']:
            return jsonify({'success': False, 'message': 'Invalid request data'})

        # Process the request
        success, message = PermissionService.process_permission_request(
            request_id=request_id,
            action=action,
            processed_by_id=session.get('teacher_id'),
            admin_notes=admin_notes
        )

        return jsonify({'success': success, 'message': message})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing request: {str(e)}'})

@permission_bp.route('/check_access')
def check_class_access():
    """Check if current user has access to a specific class/stream."""
    try:
        grade_name = request.args.get('grade')
        stream_name = request.args.get('stream')

        if not grade_name:
            return jsonify({'success': False, 'message': 'Grade parameter required'})

        teacher_id = session.get('teacher_id')
        role = get_role(session)

        # Headteacher always has access
        if role == 'headteacher':
            has_access = True
        elif role == 'classteacher':
            has_access = PermissionService.check_classteacher_permission(teacher_id, grade_name, stream_name)
        else:
            has_access = False

        return jsonify({
            'success': True,
            'has_access': has_access,
            'grade': grade_name,
            'stream': stream_name
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error checking access: {str(e)}'})


# ============================================================================
# ENHANCED FUNCTION-LEVEL PERMISSION MANAGEMENT
# ============================================================================

@permission_bp.route('/manage_functions')
@require_roles('headteacher')
@feature_required('FUNCTION_PERMISSION_MANAGEMENT')
def manage_function_permissions():
    """Enhanced permission management page for function-level permissions."""
    # Build a resilient fallback so template never explodes (previously any render error silently redirected)
    try:
        dashboard_data = EnhancedPermissionService.get_all_function_permissions_dashboard() or {}
    except Exception as service_error:
        current_app.logger.exception("Error fetching function permission dashboard data")
        dashboard_data = {}

    # Inject guaranteed keys to avoid Jinja Undefined call errors (e.g. .items() on Undefined)
    try:
        from ..models.function_permission import DefaultFunctionPermissions
        fallback_available = {
            'default_allowed': getattr(DefaultFunctionPermissions, 'DEFAULT_ALLOWED_FUNCTIONS', {}),
            'restricted': getattr(DefaultFunctionPermissions, 'RESTRICTED_FUNCTIONS', {})
        }
    except Exception as import_error:
        current_app.logger.exception("Error importing DefaultFunctionPermissions for fallback")
        fallback_available = {'default_allowed': {}, 'restricted': {}}

    safe_data = {
        'teachers': dashboard_data.get('teachers', []),
        'function_permissions': dashboard_data.get('function_permissions', []),
        'available_functions': dashboard_data.get('available_functions', fallback_available),
        'grades': dashboard_data.get('grades', []),
        'streams': dashboard_data.get('streams', []),
        'permission_stats': dashboard_data.get('permission_stats', {
            'total_permissions': len(dashboard_data.get('function_permissions', [])),
            'teachers_with_permissions': len({p.get('teacher_id') for p in dashboard_data.get('function_permissions', [])}),
            'most_granted_function': None
        })
    }

    # Final render with granular error capture so we do not hard-redirect; show user an inline error instead
    try:
        return render_template(
            'enhanced_permission_management.html',
            data=safe_data,
            current_user=session.get('teacher_id')
        )
    except Exception as render_error:
        current_app.logger.exception("Error rendering enhanced_permission_management.html")
        flash('A rendering error occurred while loading Function Permissions. Fallback view shown.', 'error')
        # Provide an ultra-minimal empty safe payload so page shell can still load
        minimal_data = {
            'teachers': [],
            'function_permissions': [],
            'available_functions': fallback_available,
            'grades': [],
            'streams': [],
            'permission_stats': {'total_permissions': 0, 'teachers_with_permissions': 0, 'most_granted_function': None}
        }
        return render_template('enhanced_permission_management.html', data=minimal_data, current_user=session.get('teacher_id'))

def _validate_grant_function():
    data = request.get_json(silent=True) or {}
    teacher_id = data.get('teacher_id')
    function_name = data.get('function_name')
    if not teacher_id or not function_name:
        missing = {}
        if not teacher_id: missing['teacher_id'] = 'required'
        if not function_name: missing['function_name'] = 'required'
        raise ValidationError('Missing required fields', missing)
    if not str(teacher_id).isdigit():
        raise ValidationError('teacher_id must be numeric')
    return {
        'teacher_id': int(teacher_id),
        'function_name': function_name,
        'scope_type': data.get('scope_type','global'),
        'grade_id': data.get('grade_id'),
        'stream_id': data.get('stream_id'),
        'expires_at': data.get('expires_at'),
        'notes': data.get('notes','')
    }

@permission_bp.route('/grant_function', methods=['POST'])
@secure_endpoint(roles=['headteacher','admin'], rate=(40,60), validator=_validate_grant_function, audit_event='permission.function.grant')
def grant_function_permission(_validated):
    v = _validated
    success, message = EnhancedPermissionService.grant_function_permission(
        teacher_id=v['teacher_id'],
        function_name=v['function_name'],
        granted_by_id=session.get('teacher_id'),
        scope_type=v['scope_type'],
        grade_id=v['grade_id'],
        stream_id=v['stream_id'],
        expires_at=v['expires_at'],
        notes=v['notes']
    )
    return jsonify({'success': success, 'message': message})

def _validate_revoke_function():
    data = request.get_json(silent=True) or {}
    teacher_id = data.get('teacher_id')
    function_name = data.get('function_name')
    if not teacher_id or not function_name:
        missing = {}
        if not teacher_id: missing['teacher_id'] = 'required'
        if not function_name: missing['function_name'] = 'required'
        raise ValidationError('Missing required fields', missing)
    return {
        'teacher_id': teacher_id,
        'function_name': function_name,
        'scope_type': data.get('scope_type','global'),
        'grade_id': data.get('grade_id'),
        'stream_id': data.get('stream_id')
    }

@permission_bp.route('/revoke_function', methods=['POST'])
@secure_endpoint(roles=['headteacher','admin'], rate=(40,60), validator=_validate_revoke_function, audit_event='permission.function.revoke')
def revoke_function_permission(_validated):
    v = _validated
    success, message = EnhancedPermissionService.revoke_function_permission(
        teacher_id=v['teacher_id'],
        function_name=v['function_name'],
        scope_type=v['scope_type'],
        grade_id=v['grade_id'],
        stream_id=v['stream_id']
    )
    return jsonify({'success': success, 'message': message})

def _validate_bulk_grant_functions():
    data = request.get_json(silent=True) or {}
    teacher_id = data.get('teacher_id')
    function_names = data.get('function_names', [])
    if not teacher_id or not function_names:
        missing = {}
        if not teacher_id: missing['teacher_id'] = 'required'
        if not function_names: missing['function_names'] = 'required'
        raise ValidationError('Missing required fields', missing)
    if not isinstance(function_names, list):
        raise ValidationError('function_names must be a list')
    return {
        'teacher_id': teacher_id,
        'function_names': function_names,
        'scope_type': data.get('scope_type','global'),
        'grade_id': data.get('grade_id'),
        'stream_id': data.get('stream_id'),
        'expires_at': data.get('expires_at'),
        'notes': data.get('notes','')
    }

@permission_bp.route('/bulk_grant_functions', methods=['POST'])
@secure_endpoint(roles=['headteacher','admin'], rate=(20,60), validator=_validate_bulk_grant_functions, audit_event='permission.function.bulk_grant')
def bulk_grant_function_permissions(_validated):
    v = _validated
    success_count, total_count, messages = EnhancedPermissionService.bulk_grant_permissions(
        teacher_id=v['teacher_id'],
        function_names=v['function_names'],
        granted_by_id=session.get('teacher_id'),
        scope_type=v['scope_type'],
        grade_id=v['grade_id'],
        stream_id=v['stream_id'],
        expires_at=v['expires_at'],
        notes=v['notes']
    )
    return jsonify({
        'success': True,
        'message': f'Granted {success_count}/{total_count} function permissions successfully',
        'success_count': success_count,
        'total_count': total_count,
        'details': messages
    })

@permission_bp.route('/teacher/<int:teacher_id>/function_permissions')
@require_roles('headteacher')
def get_teacher_function_permissions(teacher_id):
    """Get all function permissions for a specific teacher."""
    try:
        summary = EnhancedPermissionService.get_teacher_function_summary(teacher_id)

        if summary:
            return jsonify({'success': True, 'summary': summary})
        else:
            return jsonify({'success': False, 'message': 'Teacher not found'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting function permissions: {str(e)}'})

@permission_bp.route('/available_functions')
@require_roles('headteacher')
def get_available_functions():
    """Get all available functions that can be granted permissions for."""
    try:
        functions = {
            'default_allowed': DefaultFunctionPermissions.DEFAULT_ALLOWED_FUNCTIONS,
            'restricted': DefaultFunctionPermissions.RESTRICTED_FUNCTIONS
        }

        return jsonify({'success': True, 'functions': functions})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting available functions: {str(e)}'})

@permission_bp.route('/check_function_access')
def check_function_access():
    """Check if current user has access to a specific function."""
    try:
        function_name = request.args.get('function')
        grade_id = request.args.get('grade_id', type=int)
        stream_id = request.args.get('stream_id', type=int)

        if not function_name:
            return jsonify({'success': False, 'message': 'Function parameter required'})

        teacher_id = session.get('teacher_id')
        role = get_role(session)

        # Headteacher always has access
        if role == 'headteacher':
            has_access = True
        elif role == 'classteacher':
            has_access = EnhancedPermissionService.check_function_permission(
                teacher_id, function_name, grade_id, stream_id
            )
        else:
            has_access = False

        return jsonify({
            'success': True,
            'has_access': has_access,
            'function': function_name,
            'is_default_allowed': DefaultFunctionPermissions.is_default_allowed(function_name),
            'is_restricted': DefaultFunctionPermissions.is_restricted(function_name)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error checking function access: {str(e)}'})

@permission_bp.route('/class_structure')
def get_class_structure():
    """Get class structure for permission request forms."""
    try:
        from ..models.academic import Grade, Stream

        # Get all grades with their streams
        grades = Grade.query.order_by(Grade.name).all()
        structure = {}

        for grade in grades:
            streams = Stream.query.filter_by(grade_id=grade.id).order_by(Stream.name).all()
            structure[grade.name] = [
                {'id': stream.id, 'name': stream.name} for stream in streams
            ]

        return jsonify({
            'success': True,
            'structure': structure
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting class structure: {str(e)}'})

@permission_bp.route('/request', methods=['POST'])
def submit_permission_request():
    """Submit a permission request from classteacher."""
    try:
        print("=== DEBUG: Permission request received ===")

        if not is_authenticated(session):
            print("DEBUG: Authentication failed")
            return jsonify({'success': False, 'message': 'Authentication required'})

        role = get_role(session)
        print(f"DEBUG: User role: {role}")
        if role != 'classteacher':
            return jsonify({'success': False, 'message': 'Only classteachers can submit permission requests'})

        data = request.get_json()
        print(f"DEBUG: Request data: {data}")

        grade_name = data.get('grade_name')
        stream_name = data.get('stream_name')
        reason = data.get('reason')

        print(f"DEBUG: Parsed - Grade: {grade_name}, Stream: {stream_name}, Reason length: {len(reason) if reason else 0}")

        if not grade_name or not reason:
            print("DEBUG: Missing required fields")
            return jsonify({'success': False, 'message': 'Grade and reason are required'})

        teacher_id = session.get('teacher_id')
        print(f"DEBUG: Teacher ID: {teacher_id}")

        # Find grade and stream IDs
        from ..models.academic import Grade, Stream
        grade = Grade.query.filter_by(name=grade_name).first()
        print(f"DEBUG: Found grade: {grade}")
        if not grade:
            return jsonify({'success': False, 'message': 'Invalid grade selected'})

        stream = None
        if stream_name:
            stream = Stream.query.filter_by(name=stream_name, grade_id=grade.id).first()
            print(f"DEBUG: Found stream: {stream}")
            if not stream:
                return jsonify({'success': False, 'message': 'Invalid stream selected'})

        # Create permission request
        print("DEBUG: Calling PermissionService.submit_permission_request")
        success, message = PermissionService.submit_permission_request(
            teacher_id=teacher_id,
            grade_name=grade_name,
            stream_name=stream_name,
            reason=reason
        )

        print(f"DEBUG: Service result - Success: {success}, Message: {message}")
        return jsonify({'success': success, 'message': message})

    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error submitting request: {str(e)}'})

@permission_bp.route('/my_permissions')
def my_permissions():
    """View current user's permissions."""
    try:
        if not is_authenticated(session):
            return redirect(url_for('auth.classteacher_login'))

        teacher_id = session.get('teacher_id')
        role = get_role(session)

        if role == 'classteacher':
            # Get class permissions
            class_permissions = PermissionService.get_teacher_assigned_classes(teacher_id)

            # Get function permissions
            function_permissions = EnhancedPermissionService.get_teacher_function_summary(teacher_id)

            return render_template('my_permissions.html',
                                 class_permissions=class_permissions,
                                 function_permissions=function_permissions,
                                 teacher_id=teacher_id)
        else:
            flash('Access denied', 'error')
            return redirect(url_for('auth.classteacher_login'))

    except Exception as e:
        flash(f'Error loading permissions: {str(e)}', 'error')
        return redirect(url_for('classteacher.dashboard'))

@permission_bp.route('/request_function', methods=['POST'])
def submit_function_permission_request():
    """Submit a function permission request from classteacher."""
    try:
        if not is_authenticated(session):
            return jsonify({'success': False, 'message': 'Authentication required'})

        role = get_role(session)
        if role != 'classteacher':
            return jsonify({'success': False, 'message': 'Only classteachers can submit function permission requests'})

        data = request.get_json()
        function_name = data.get('function_name')
        reason = data.get('reason')
        scope = data.get('scope', 'global')

        if not function_name or not reason:
            return jsonify({'success': False, 'message': 'Function name and reason are required'})

        teacher_id = session.get('teacher_id')

        # Check if function is actually restricted
        if not DefaultFunctionPermissions.is_restricted(function_name):
            return jsonify({'success': False, 'message': 'This function does not require special permission'})

        # Create a function permission request (we'll store it as a note in the existing system for now)
        # In a full implementation, you'd create a separate FunctionPermissionRequest model
        from ..models.user import Teacher
        teacher = Teacher.query.get(teacher_id)

        # Create a function permission request using a simple approach
        # For now, we'll store it as a note in the database or log it
        try:
            # Create a simple function request record
            from ..models.permission import PermissionRequest
            from ..extensions import db

            # Create a special permission request for function access
            function_request = PermissionRequest(
                teacher_id=teacher_id,
                grade_id=None,  # No specific grade for function permissions
                stream_id=None,  # No specific stream for function permissions
                reason=f"FUNCTION PERMISSION REQUEST\\n\\nFunction: {function_name}\\nScope: {scope}\\nReason: {reason}",
                status='pending'
            )

            db.session.add(function_request)
            db.session.commit()

            success = True
            message = f"Function permission request for '{function_name}' submitted successfully"

        except Exception as e:
            db.session.rollback()
            success = False
            message = f"Failed to submit function request: {str(e)}"

        if success:
            return jsonify({
                'success': True,
                'message': f'Function permission request for "{function_name}" submitted successfully'
            })
        else:
            return jsonify({'success': False, 'message': message})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error submitting function request: {str(e)}'})


# ============================================================================
# ENHANCED PERMISSION MANAGEMENT WITH DIRECT GRANTING AND EXPIRATION
# ============================================================================

def _validate_direct_grant():
    data = request.get_json(silent=True) or {}
    teacher_id = data.get('teacher_id')
    grade_id = data.get('grade_id')
    stream_id = data.get('stream_id')
    duration_key = data.get('duration_key','1_month')
    notes = data.get('notes','')
    missing = {}
    if not teacher_id: missing['teacher_id'] = 'required'
    if not grade_id: missing['grade_id'] = 'required'
    if missing:
        raise ValidationError('Missing required fields', missing)
    if duration_key not in EnhancedPermissionManagementService.DURATION_OPTIONS:
        raise ValidationError('Invalid duration_key')
    if notes and len(notes) > 500:
        raise ValidationError('notes too long (max 500 chars)')
    return {'teacher_id': teacher_id, 'grade_id': grade_id, 'stream_id': stream_id, 'duration_key': duration_key, 'notes': notes}

@permission_bp.route('/direct_grant', methods=['POST'])
@secure_endpoint(roles=['headteacher','admin'], rate=(30,60), validator=_validate_direct_grant, audit_event='permission.direct.grant')
def direct_grant_permission(_validated):
    v = _validated
    result = EnhancedPermissionManagementService.grant_direct_permission(
        teacher_id=v['teacher_id'],
        grade_id=v['grade_id'],
        stream_id=v['stream_id'],
        granted_by_id=session.get('teacher_id'),
        duration_key=v['duration_key'],
        notes=v['notes']
    )
    return jsonify(result)

def _validate_bulk_direct_grant():
    data = request.get_json(silent=True) or {}
    teacher_id = data.get('teacher_id')
    class_assignments = data.get('class_assignments', [])
    duration_key = data.get('duration_key','1_month')
    notes = data.get('notes','')
    missing = {}
    if not teacher_id: missing['teacher_id'] = 'required'
    if not class_assignments: missing['class_assignments'] = 'required'
    if missing:
        raise ValidationError('Missing required fields', missing)
    if not isinstance(class_assignments, list):
        raise ValidationError('class_assignments must be a list')
    # Basic structure validation
    for idx, assignment in enumerate(class_assignments):
        if 'grade_id' not in assignment:
            raise ValidationError(f'missing grade_id in assignment {idx}')
    if duration_key not in EnhancedPermissionManagementService.DURATION_OPTIONS:
        raise ValidationError('Invalid duration_key')
    if notes and len(notes) > 500:
        raise ValidationError('notes too long (max 500 chars)')
    return {'teacher_id': teacher_id, 'class_assignments': class_assignments, 'duration_key': duration_key, 'notes': notes}

@permission_bp.route('/bulk_direct_grant', methods=['POST'])
@secure_endpoint(roles=['headteacher','admin'], rate=(15,60), validator=_validate_bulk_direct_grant, audit_event='permission.direct.bulk_grant')
def bulk_direct_grant_permissions(_validated):
    v = _validated
    result = EnhancedPermissionManagementService.bulk_grant_permissions(
        teacher_id=v['teacher_id'],
        class_assignments=v['class_assignments'],
        granted_by_id=session.get('teacher_id'),
        duration_key=v['duration_key'],
        notes=v['notes']
    )
    return jsonify(result)

def _validate_extend_permission():
    data = request.get_json(silent=True) or {}
    permission_id = data.get('permission_id')
    duration_key = data.get('duration_key','1_month')
    if not permission_id:
        raise ValidationError('Missing required fields', {'permission_id':'required'})
    if duration_key not in EnhancedPermissionManagementService.DURATION_OPTIONS:
        raise ValidationError('Invalid duration_key')
    return {'permission_id': permission_id, 'duration_key': duration_key}

@permission_bp.route('/extend_permission', methods=['POST'])
@secure_endpoint(roles=['headteacher','admin'], rate=(40,60), validator=_validate_extend_permission, audit_event='permission.extend')
def extend_permission(_validated):
    v = _validated
    result = EnhancedPermissionManagementService.extend_permission(
        permission_id=v['permission_id'],
        duration_key=v['duration_key'],
        extended_by_id=session.get('teacher_id')
    )
    return jsonify(result)

@permission_bp.route('/expiring_permissions')
@require_roles('headteacher')
def get_expiring_permissions():
    """Get permissions that will expire soon."""
    try:
        days_ahead = request.args.get('days_ahead', 7, type=int)

        expiring_permissions = EnhancedPermissionManagementService.get_expiring_permissions(days_ahead)

        return jsonify({
            'success': True,
            'expiring_permissions': expiring_permissions,
            'count': len(expiring_permissions)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting expiring permissions: {str(e)}'})

@permission_bp.route('/permission_statistics')
@require_roles('headteacher')
def get_permission_statistics():
    """Get comprehensive permission statistics."""
    try:
        stats = EnhancedPermissionManagementService.get_permission_statistics()

        return jsonify({
            'success': True,
            'statistics': stats
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting statistics: {str(e)}'})

@permission_bp.route('/duration_options')
@require_roles('headteacher')
def get_duration_options():
    """Get available duration options for permissions."""
    try:
        return jsonify({
            'success': True,
            'duration_options': EnhancedPermissionManagementService.DURATION_OPTIONS
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting duration options: {str(e)}'})
