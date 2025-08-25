"""
Enhanced permission service for function-level access control.
Provides granular permission management for classteacher functions.
"""
from ..models.function_permission import FunctionPermission, DefaultFunctionPermissions
from ..models.permission import ClassTeacherPermission
from ..models.user import Teacher
from ..models.academic import Grade, Stream
from ..extensions import db
from flask import session
from functools import wraps

class EnhancedPermissionService:
    """Enhanced service for managing function-level permissions."""
    
    @staticmethod
    def check_function_permission(teacher_id, function_name, grade_id=None, stream_id=None):
        """
        Check if a teacher has permission to access a specific function.

        Args:
            teacher_id: ID of the teacher
            function_name: Name of the function to check
            grade_id: Optional grade ID for scoped permissions
            stream_id: Optional stream ID for scoped permissions

        Returns:
            Boolean indicating if access is allowed
        """
        try:
            print(f"🔍 Enhanced Permission Service Debug:")
            print(f"  Function: {function_name}")
            print(f"  Teacher ID: {teacher_id}")
            
            # Check if function is allowed by default
            print(f"  Checking if {function_name} is in default allowed functions...")
            
            try:
                is_default_allowed = DefaultFunctionPermissions.is_default_allowed(function_name)
                print(f"  Is default allowed: {is_default_allowed}")
            except Exception as e:
                print(f"  🚨 Error checking default allowed: {e}")
                import traceback
                traceback.print_exc()
                is_default_allowed = False
            
            if is_default_allowed:
                print(f"  ✅ Allowing access (default allowed)")
                return True

            # Check if function requires explicit permission
            print(f"  Checking if {function_name} is restricted...")
            try:
                is_restricted = DefaultFunctionPermissions.is_restricted(function_name)
                print(f"  Is restricted: {is_restricted}")
            except Exception as e:
                print(f"  🚨 Error checking restricted: {e}")
                import traceback
                traceback.print_exc()
                is_restricted = False
            
            if is_restricted:
                print(f"  Checking explicit permission...")
                try:
                    has_explicit = FunctionPermission.has_function_permission(
                        teacher_id, function_name, grade_id, stream_id
                    )
                    print(f"  Has explicit permission: {has_explicit}")
                    return has_explicit
                except Exception as e:
                    print(f"  🚨 Error checking explicit permission: {e}")
                    import traceback
                    traceback.print_exc()
                    return False

            # Unknown function - deny by default
            print(f"  ❌ Unknown function - denying by default")
            return False

        except Exception as e:
            # Fallback: If there's any database error, handle gracefully
            print(f"🚨 Permission check error for {function_name}: {e}")
            import traceback
            traceback.print_exc()

            # For safety, allow default functions and deny restricted ones
            try:
                print(f"  Attempting fallback permission check...")
                if DefaultFunctionPermissions.is_default_allowed(function_name):
                    print(f"  ✅ Fallback: Allowing default function")
                    return True
                else:
                    # Deny access to restricted functions if there's a permission system error
                    print(f"  ❌ Fallback: Denying access to {function_name} due to permission system error")
                    return False  # Proper security: deny access when in doubt
            except Exception as fallback_error:
                print(f"🚨 Fallback permission check also failed: {fallback_error}")
                import traceback
                traceback.print_exc()
                return False
    
    @staticmethod
    def grant_function_permission(teacher_id, function_name, granted_by_id, 
                                 scope_type='global', grade_id=None, stream_id=None,
                                 expires_at=None, notes=None):
        """
        Grant a function permission to a teacher.
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            # Validate function name
            if not DefaultFunctionPermissions.is_restricted(function_name):
                return False, f"Function '{function_name}' does not require explicit permission"
            
            # Get function category
            function_category = DefaultFunctionPermissions.get_function_category(function_name)
            
            # Grant the permission
            permission = FunctionPermission.grant_function_permission(
                teacher_id=teacher_id,
                function_name=function_name,
                function_category=function_category,
                granted_by_id=granted_by_id,
                scope_type=scope_type,
                grade_id=grade_id,
                stream_id=stream_id,
                expires_at=expires_at,
                notes=notes
            )
            
            if permission:
                teacher = Teacher.query.get(teacher_id)
                scope_desc = EnhancedPermissionService._get_scope_description(scope_type, grade_id, stream_id)
                return True, f"Permission '{function_name}' granted to {teacher.username} {scope_desc}"
            else:
                return False, "Failed to grant permission"
                
        except Exception as e:
            return False, f"Error granting permission: {str(e)}"
    
    @staticmethod
    def revoke_function_permission(teacher_id, function_name, scope_type='global', 
                                  grade_id=None, stream_id=None):
        """
        Revoke a function permission from a teacher.
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            success = FunctionPermission.revoke_function_permission(
                teacher_id, function_name, scope_type, grade_id, stream_id
            )
            
            if success:
                teacher = Teacher.query.get(teacher_id)
                scope_desc = EnhancedPermissionService._get_scope_description(scope_type, grade_id, stream_id)
                return True, f"Permission '{function_name}' revoked from {teacher.username} {scope_desc}"
            else:
                return False, "Permission not found or already revoked"
                
        except Exception as e:
            return False, f"Error revoking permission: {str(e)}"
    
    @staticmethod
    def bulk_grant_permissions(teacher_id, function_names, granted_by_id, 
                              scope_type='global', grade_id=None, stream_id=None,
                              expires_at=None, notes=None):
        """
        Grant multiple function permissions to a teacher at once.
        
        Returns:
            Tuple (success_count: int, total_count: int, messages: list)
        """
        success_count = 0
        messages = []
        
        for function_name in function_names:
            success, message = EnhancedPermissionService.grant_function_permission(
                teacher_id, function_name, granted_by_id, scope_type, 
                grade_id, stream_id, expires_at, notes
            )
            
            if success:
                success_count += 1
            
            messages.append(message)
        
        return success_count, len(function_names), messages
    
    @staticmethod
    def get_teacher_function_summary(teacher_id):
        """
        Get a comprehensive summary of a teacher's function permissions.
        
        Returns:
            Dictionary with permission details
        """
        try:
            teacher = Teacher.query.get(teacher_id)
            if not teacher:
                return None
            
            # Get explicit permissions
            explicit_permissions = FunctionPermission.get_teacher_function_permissions(teacher_id)
            
            # Organize permissions by category
            permissions_by_category = {}
            for perm in explicit_permissions:
                category = perm.function_category
                if category not in permissions_by_category:
                    permissions_by_category[category] = []
                
                permissions_by_category[category].append({
                    'function_name': perm.function_name,
                    'scope_type': perm.scope_type,
                    'grade_name': perm.grade.name if perm.grade else None,
                    'stream_name': perm.stream.name if perm.stream else None,
                    'granted_at': perm.granted_at,
                    'expires_at': perm.expires_at,
                    'notes': perm.notes
                })
            
            # Get default allowed functions
            default_functions = {}
            for category, functions in DefaultFunctionPermissions.DEFAULT_ALLOWED_FUNCTIONS.items():
                default_functions[category] = functions
            
            return {
                'teacher_id': teacher_id,
                'teacher_name': teacher.full_name or teacher.username,
                'teacher_username': teacher.username,
                'explicit_permissions': permissions_by_category,
                'default_allowed_functions': default_functions,
                'total_explicit_permissions': len(explicit_permissions)
            }
            
        except Exception as e:
            print(f"Error getting teacher function summary: {e}")
            return None
    
    @staticmethod
    def get_all_function_permissions_dashboard():
        """
        Get comprehensive permission data for headteacher dashboard.
        
        Returns:
            Dictionary with all permission management data
        """
        try:
            # Get all teachers (excluding headteacher)
            teachers = Teacher.query.filter(Teacher.role != 'headteacher').all()
            
            # Get all function permissions
            all_permissions = FunctionPermission.get_all_function_permissions_summary()
            
            # Get available functions by category
            available_functions = {
                'default_allowed': DefaultFunctionPermissions.DEFAULT_ALLOWED_FUNCTIONS,
                'restricted': DefaultFunctionPermissions.RESTRICTED_FUNCTIONS
            }
            
            # Get grades and streams for scoped permissions
            grades = Grade.query.all()
            streams = Stream.query.all()
            
            return {
                'teachers': [
                    {
                        'id': t.id, 
                        'name': t.full_name or t.username, 
                        'username': t.username,
                        'role': t.role
                    } for t in teachers
                ],
                'function_permissions': all_permissions,
                'available_functions': available_functions,
                'grades': [{'id': g.id, 'name': g.name} for g in grades],
                'streams': [{'id': s.id, 'name': s.name, 'grade_id': s.grade_id} for s in streams],
                'permission_stats': {
                    'total_permissions': len(all_permissions),
                    'teachers_with_permissions': len(set(p['teacher_id'] for p in all_permissions)),
                    'most_granted_function': EnhancedPermissionService._get_most_granted_function(all_permissions)
                }
            }
            
        except Exception as e:
            print(f"Error getting function permissions dashboard: {e}")
            return {}
    
    @staticmethod
    def _get_scope_description(scope_type, grade_id, stream_id):
        """Get human-readable description of permission scope."""
        if scope_type == 'global':
            return "(globally)"
        elif scope_type == 'grade' and grade_id:
            grade = Grade.query.get(grade_id)
            return f"(for {grade.name})" if grade else "(for unknown grade)"
        elif scope_type == 'stream' and grade_id and stream_id:
            grade = Grade.query.get(grade_id)
            stream = Stream.query.get(stream_id)
            if grade and stream:
                return f"(for {grade.name} {stream.name})"
            return "(for unknown class)"
        return ""
    
    @staticmethod
    def _get_most_granted_function(permissions):
        """Get the most frequently granted function."""
        if not permissions:
            return None
        
        function_counts = {}
        for perm in permissions:
            func = perm['function_name']
            function_counts[func] = function_counts.get(func, 0) + 1
        
        return max(function_counts.items(), key=lambda x: x[1])[0] if function_counts else None


def function_permission_required(function_name):
    """
    Decorator to check function-level permissions for classteacher routes.
    
    Usage:
        @function_permission_required('manage_students')
        def manage_students():
            # Function implementation
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get current user info
            teacher_id = session.get('teacher_id')
            role = session.get('role')
            
            # Headteacher and universal access always allowed
            if role == 'headteacher':
                return f(*args, **kwargs)
            
            if role == 'headteacher' and session.get('headteacher_universal_access'):
                return f(*args, **kwargs)
            
            # For classteachers, check function permission
            if role == 'classteacher' and teacher_id:
                # Get grade/stream context if available
                grade_id = session.get('current_grade_id')
                stream_id = session.get('current_stream_id')
                
                # Check permission
                has_permission = EnhancedPermissionService.check_function_permission(
                    teacher_id, function_name, grade_id, stream_id
                )
                
                if has_permission:
                    return f(*args, **kwargs)
                else:
                    # Redirect to permission request page or show error
                    from flask import flash, redirect, url_for
                    flash(f"You don't have permission to access '{function_name}'. Please request permission from the headteacher.", "error")
                    return redirect(url_for('classteacher.dashboard'))
            
            # Default: redirect to login
            from flask import redirect, url_for
            return redirect(url_for('auth.classteacher_login'))
        
        return decorated_function
    return decorator


def check_function_access(function_name, teacher_id=None, grade_id=None, stream_id=None):
    """
    Helper function to check function access without decorator.
    
    Returns:
        Boolean indicating if access is allowed
    """
    # Use current session if teacher_id not provided
    if teacher_id is None:
        teacher_id = session.get('teacher_id')
        role = session.get('role')
        
        # Headteacher always has access
        if role == 'headteacher':
            return True
        
        if role != 'classteacher':
            return False
    
    return EnhancedPermissionService.check_function_permission(
        teacher_id, function_name, grade_id, stream_id
    )
