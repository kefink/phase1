"""
Permission management views for headteacher delegation system.
Allows headteacher to grant/revoke classteacher permissions for specific classes/streams.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from ..models import ClassTeacherPermission, Teacher, Grade, Stream
from ..services.permission_service import PermissionService
from ..services.enhanced_permission_service import EnhancedPermissionService
from ..services import is_authenticated, get_role
from ..models.function_permission import DefaultFunctionPermissions
from ..extensions import csrf
from functools import wraps

# Create blueprint for permission management
permission_bp = Blueprint('permission', __name__, url_prefix='/permission')

def headteacher_required(f):
    """Decorator to require headteacher authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session) or get_role(session) != 'headteacher':
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@permission_bp.route('/manage')
@headteacher_required
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

@permission_bp.route('/grant', methods=['POST'])
@headteacher_required
def grant_permission():
    """Grant permission to a teacher for a specific class/stream."""
    try:
        data = request.get_json()
        teacher_id = data.get('teacher_id')
        grade_name = data.get('grade_name')
        stream_name = data.get('stream_name')  # None for single classes
        notes = data.get('notes', '')
        
        if not teacher_id or not grade_name:
            return jsonify({'success': False, 'message': 'Teacher and grade are required'})
        
        # Grant permission
        success, message = PermissionService.grant_permission(
            teacher_id=teacher_id,
            grade_name=grade_name,
            stream_name=stream_name,
            granted_by_id=session.get('teacher_id'),
            notes=notes
        )
        
        return jsonify({'success': success, 'message': message})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error granting permission: {str(e)}'})

@permission_bp.route('/revoke', methods=['POST'])
@headteacher_required
def revoke_permission():
    """Revoke permission from a teacher for a specific class/stream."""
    try:
        data = request.get_json()
        teacher_id = data.get('teacher_id')
        grade_name = data.get('grade_name')
        stream_name = data.get('stream_name')  # None for single classes
        
        if not teacher_id or not grade_name:
            return jsonify({'success': False, 'message': 'Teacher and grade are required'})
        
        # Revoke permission
        success, message = PermissionService.revoke_permission(
            teacher_id=teacher_id,
            grade_name=grade_name,
            stream_name=stream_name
        )
        
        return jsonify({'success': success, 'message': message})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error revoking permission: {str(e)}'})

@permission_bp.route('/teacher/<int:teacher_id>/permissions')
@headteacher_required
def get_teacher_permissions(teacher_id):
    """Get all permissions for a specific teacher."""
    try:
        permissions = PermissionService.get_teacher_assigned_classes(teacher_id)
        return jsonify({'success': True, 'permissions': permissions})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting permissions: {str(e)}'})

# Removed duplicate - using the enhanced version below

@permission_bp.route('/bulk_grant', methods=['POST'])
@headteacher_required
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
@headteacher_required
def get_pending_requests():
    """Get all pending permission requests for headteacher review."""
    try:
        requests = PermissionService.get_pending_requests()
        return jsonify({'success': True, 'requests': requests})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting requests: {str(e)}'})

@permission_bp.route('/process_request', methods=['POST'])
@headteacher_required
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
@headteacher_required
def manage_function_permissions():
    """Enhanced permission management page for function-level permissions."""
    try:
        # Get comprehensive function permission data
        dashboard_data = EnhancedPermissionService.get_all_function_permissions_dashboard()

        return render_template('enhanced_permission_management.html',
                             data=dashboard_data,
                             current_user=session.get('teacher_id'))

    except Exception as e:
        flash(f'Error loading function permission management: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@permission_bp.route('/grant_function', methods=['POST'])
@headteacher_required
def grant_function_permission():
    """Grant a specific function permission to a teacher."""
    try:
        data = request.get_json()
        teacher_id = data.get('teacher_id')
        function_name = data.get('function_name')
        scope_type = data.get('scope_type', 'global')
        grade_id = data.get('grade_id')
        stream_id = data.get('stream_id')
        expires_at = data.get('expires_at')  # Optional expiration
        notes = data.get('notes', '')

        if not teacher_id or not function_name:
            return jsonify({'success': False, 'message': 'Teacher and function are required'})

        # Grant function permission
        success, message = EnhancedPermissionService.grant_function_permission(
            teacher_id=teacher_id,
            function_name=function_name,
            granted_by_id=session.get('teacher_id'),
            scope_type=scope_type,
            grade_id=grade_id,
            stream_id=stream_id,
            expires_at=expires_at,
            notes=notes
        )

        return jsonify({'success': success, 'message': message})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error granting function permission: {str(e)}'})

@permission_bp.route('/revoke_function', methods=['POST'])
@headteacher_required
def revoke_function_permission():
    """Revoke a specific function permission from a teacher."""
    try:
        data = request.get_json()
        teacher_id = data.get('teacher_id')
        function_name = data.get('function_name')
        scope_type = data.get('scope_type', 'global')
        grade_id = data.get('grade_id')
        stream_id = data.get('stream_id')

        if not teacher_id or not function_name:
            return jsonify({'success': False, 'message': 'Teacher and function are required'})

        # Revoke function permission
        success, message = EnhancedPermissionService.revoke_function_permission(
            teacher_id=teacher_id,
            function_name=function_name,
            scope_type=scope_type,
            grade_id=grade_id,
            stream_id=stream_id
        )

        return jsonify({'success': success, 'message': message})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error revoking function permission: {str(e)}'})

@permission_bp.route('/bulk_grant_functions', methods=['POST'])
@headteacher_required
def bulk_grant_function_permissions():
    """Grant multiple function permissions to a teacher at once."""
    try:
        data = request.get_json()
        teacher_id = data.get('teacher_id')
        function_names = data.get('function_names', [])
        scope_type = data.get('scope_type', 'global')
        grade_id = data.get('grade_id')
        stream_id = data.get('stream_id')
        expires_at = data.get('expires_at')
        notes = data.get('notes', '')

        if not teacher_id or not function_names:
            return jsonify({'success': False, 'message': 'Teacher and functions are required'})

        # Bulk grant permissions
        success_count, total_count, messages = EnhancedPermissionService.bulk_grant_permissions(
            teacher_id=teacher_id,
            function_names=function_names,
            granted_by_id=session.get('teacher_id'),
            scope_type=scope_type,
            grade_id=grade_id,
            stream_id=stream_id,
            expires_at=expires_at,
            notes=notes
        )

        return jsonify({
            'success': True,
            'message': f'Granted {success_count}/{total_count} function permissions successfully',
            'success_count': success_count,
            'total_count': total_count,
            'details': messages
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error in bulk grant: {str(e)}'})

@permission_bp.route('/teacher/<int:teacher_id>/function_permissions')
@headteacher_required
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
@headteacher_required
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
            class_permissions = PermissionService.get_teacher_permissions(teacher_id)

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
