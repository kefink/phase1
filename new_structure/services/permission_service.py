"""
Permission management service for the delegation-based access control system.
Handles permission granting, revoking, and checking for classteachers.
"""
from ..models import ClassTeacherPermission, PermissionRequest, Teacher, Grade, Stream
from ..extensions import db
from flask import session

class PermissionService:
    """Service class for managing classteacher permissions."""
    
    @staticmethod
    def check_classteacher_permission(teacher_id, grade_name, stream_name=None):
        """
        Check if a classteacher has permission to access a specific class/stream.
        
        Args:
            teacher_id: ID of the teacher
            grade_name: Name of the grade (e.g., "Grade 1", "PP1")
            stream_name: Name of the stream (e.g., "A", "B") or None for single classes
            
        Returns:
            Boolean indicating if permission exists
        """
        try:
            # Get grade object
            grade = Grade.query.filter_by(name=grade_name).first()
            if not grade:
                return False
            
            # Get stream object if specified
            stream = None
            if stream_name:
                stream = Stream.query.filter_by(name=stream_name, grade_id=grade.id).first()
                if not stream:
                    return False
            
            # Check permission
            return ClassTeacherPermission.has_permission(
                teacher_id=teacher_id,
                grade_id=grade.id,
                stream_id=stream.id if stream else None
            )
            
        except Exception as e:
            print(f"Error checking permission: {e}")
            return False
    
    @staticmethod
    def get_teacher_assigned_classes(teacher_id):
        """
        Get all classes/streams that a teacher has permission to manage.
        
        Args:
            teacher_id: ID of the teacher
            
        Returns:
            List of dictionaries with class information
        """
        try:
            permissions = ClassTeacherPermission.get_teacher_permissions(teacher_id)
            classes = []
            
            for perm in permissions:
                class_info = {
                    'grade_name': perm.grade.name,
                    'grade_id': perm.grade_id,
                    'stream_name': perm.stream.name if perm.stream else None,
                    'stream_id': perm.stream_id,
                    'granted_at': perm.granted_at,
                    'permission_id': perm.id,
                    'display_name': f"{perm.grade.name}" + (f" Stream {perm.stream.name}" if perm.stream else "")
                }
                classes.append(class_info)
            
            return classes
            
        except Exception as e:
            print(f"Error getting teacher classes: {e}")
            return []
    
    @staticmethod
    def grant_permission(teacher_id, grade_name, stream_name, granted_by_id, notes=None):
        """
        Grant permission to a teacher for a specific class/stream.
        
        Args:
            teacher_id: ID of teacher receiving permission
            grade_name: Name of the grade
            stream_name: Name of the stream (None for single classes)
            granted_by_id: ID of headteacher granting permission
            notes: Optional notes
            
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            # Get grade
            grade = Grade.query.filter_by(name=grade_name).first()
            if not grade:
                return False, f"Grade '{grade_name}' not found"
            
            # Get stream if specified
            stream = None
            if stream_name:
                stream = Stream.query.filter_by(name=stream_name, grade_id=grade.id).first()
                if not stream:
                    return False, f"Stream '{stream_name}' not found in {grade_name}"
            
            # Grant permission
            permission = ClassTeacherPermission.grant_permission(
                teacher_id=teacher_id,
                grade_id=grade.id,
                stream_id=stream.id if stream else None,
                granted_by_id=granted_by_id,
                notes=notes
            )
            
            if permission:
                return True, "Permission granted successfully"
            else:
                return False, "Failed to grant permission"
                
        except Exception as e:
            return False, f"Error granting permission: {str(e)}"
    
    @staticmethod
    def revoke_permission(teacher_id, grade_name, stream_name):
        """
        Revoke permission from a teacher for a specific class/stream.
        
        Args:
            teacher_id: ID of teacher losing permission
            grade_name: Name of the grade
            stream_name: Name of the stream (None for single classes)
            
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            # Get grade
            grade = Grade.query.filter_by(name=grade_name).first()
            if not grade:
                return False, f"Grade '{grade_name}' not found"
            
            # Get stream if specified
            stream = None
            if stream_name:
                stream = Stream.query.filter_by(name=stream_name, grade_id=grade.id).first()
                if not stream:
                    return False, f"Stream '{stream_name}' not found in {grade_name}"
            
            # Revoke permission
            success = ClassTeacherPermission.revoke_permission(
                teacher_id=teacher_id,
                grade_id=grade.id,
                stream_id=stream.id if stream else None
            )
            
            if success:
                return True, "Permission revoked successfully"
            else:
                return False, "Permission not found or already revoked"
                
        except Exception as e:
            return False, f"Error revoking permission: {str(e)}"
    
    @staticmethod
    def get_all_class_assignments():
        """
        Get all possible class assignments organized by education level.

        Returns:
            Dictionary organized by education level with class assignment details
        """
        try:
            # Education level mapping with proper ordering
            education_levels = {
                'lower_primary': {
                    'name': 'Lower Primary',
                    'grades': ['PP1', 'PP2', 'Grade 1', 'Grade 2', 'Grade 3'],
                    'order': 1
                },
                'upper_primary': {
                    'name': 'Upper Primary',
                    'grades': ['Grade 4', 'Grade 5', 'Grade 6'],
                    'order': 2
                },
                'junior_secondary': {
                    'name': 'Junior Secondary',
                    'grades': ['Grade 7', 'Grade 8', 'Grade 9'],
                    'order': 3
                }
            }

            # Get all grades with their streams, ordered properly
            grades = Grade.query.order_by(Grade.name).all()
            organized_assignments = {}

            # Initialize education levels
            for level_key, level_info in education_levels.items():
                organized_assignments[level_key] = {
                    'name': level_info['name'],
                    'order': level_info['order'],
                    'classes': []
                }

            for grade in grades:
                # Determine education level
                education_level = None
                for level_key, level_info in education_levels.items():
                    if grade.name in level_info['grades']:
                        education_level = level_key
                        break

                if not education_level:
                    education_level = 'other'
                    if 'other' not in organized_assignments:
                        organized_assignments['other'] = {
                            'name': 'Other',
                            'order': 4,
                            'classes': []
                        }

                streams = Stream.query.filter_by(grade_id=grade.id).order_by(Stream.name).all()

                if streams:
                    # Multi-stream grade
                    for stream in streams:
                        class_info = {
                            'grade_id': grade.id,
                            'grade_name': grade.name,
                            'stream_id': stream.id,
                            'stream_name': stream.name,
                            'class_name': f"{grade.name} {stream.name}",
                            'is_multi_stream': True,
                            'education_level': education_level,
                            'type': 'multi_stream'
                        }
                        organized_assignments[education_level]['classes'].append(class_info)
                else:
                    # Single class grade
                    class_info = {
                        'grade_id': grade.id,
                        'grade_name': grade.name,
                        'stream_id': None,
                        'stream_name': None,
                        'class_name': grade.name,
                        'is_multi_stream': False,
                        'education_level': education_level,
                        'type': 'single_class'
                    }
                    organized_assignments[education_level]['classes'].append(class_info)

            # Sort classes within each education level
            for level_key in organized_assignments:
                organized_assignments[level_key]['classes'].sort(
                    key=lambda x: (x['grade_name'], x['stream_name'] or '')
                )

            return organized_assignments

        except Exception as e:
            print(f"Error getting class assignments: {e}")
            return {}
    
    @staticmethod
    def get_permission_dashboard_data(page=1, per_page=10, teacher_filter='', role_filter=''):
        """
        Get comprehensive data for the headteacher permission management dashboard with pagination.

        Args:
            page: Page number for pagination
            per_page: Number of items per page
            teacher_filter: Filter by teacher name/username
            role_filter: Filter by teacher role

        Returns:
            Dictionary with all permission-related data including pagination info
        """
        try:
            # Build teacher query with filters
            teacher_query = Teacher.query.filter(Teacher.role != 'headteacher')

            if teacher_filter:
                teacher_query = teacher_query.filter(
                    db.or_(
                        Teacher.username.ilike(f'%{teacher_filter}%'),
                        Teacher.full_name.ilike(f'%{teacher_filter}%')
                    )
                )

            if role_filter:
                teacher_query = teacher_query.filter(Teacher.role == role_filter)

            # Order teachers by name
            teacher_query = teacher_query.order_by(Teacher.full_name, Teacher.username)

            # Apply pagination
            teachers_paginated = teacher_query.paginate(
                page=page, per_page=per_page, error_out=False
            )

            # Get all class assignments organized by education level
            class_assignments = PermissionService.get_all_class_assignments()

            # Get current permissions
            current_permissions = ClassTeacherPermission.get_all_permissions_summary()

            # Get pending requests
            pending_requests = PermissionRequest.query.filter_by(status='pending').all()

            # Calculate statistics
            total_teachers = Teacher.query.filter(Teacher.role != 'headteacher').count()
            total_permissions = len(current_permissions)
            teachers_with_permissions = len(set(p['teacher_id'] for p in current_permissions))

            return {
                'teachers': [
                    {
                        'id': t.id,
                        'name': t.full_name or t.username,
                        'username': t.username,
                        'role': t.role,
                        'full_name': t.full_name
                    } for t in teachers_paginated.items
                ],
                'pagination': {
                    'page': teachers_paginated.page,
                    'pages': teachers_paginated.pages,
                    'per_page': teachers_paginated.per_page,
                    'total': teachers_paginated.total,
                    'has_prev': teachers_paginated.has_prev,
                    'has_next': teachers_paginated.has_next,
                    'prev_num': teachers_paginated.prev_num,
                    'next_num': teachers_paginated.next_num
                },
                'class_assignments': class_assignments,
                'current_permissions': current_permissions,
                'pending_requests': len(pending_requests),
                'statistics': {
                    'total_teachers': total_teachers,
                    'total_permissions': total_permissions,
                    'teachers_with_permissions': teachers_with_permissions,
                    'pending_requests': len(pending_requests)
                },
                'filters': {
                    'teacher_filter': teacher_filter,
                    'role_filter': role_filter
                }
            }

        except Exception as e:
            print(f"Error getting dashboard data: {e}")
            return {
                'teachers': [],
                'pagination': {
                    'page': 1, 'pages': 1, 'per_page': per_page, 'total': 0,
                    'has_prev': False, 'has_next': False, 'prev_num': None, 'next_num': None
                },
                'class_assignments': {},
                'current_permissions': [],
                'pending_requests': 0,
                'statistics': {
                    'total_teachers': 0, 'total_permissions': 0,
                    'teachers_with_permissions': 0, 'pending_requests': 0
                },
                'filters': {'teacher_filter': teacher_filter, 'role_filter': role_filter}
            }

    @staticmethod
    def submit_permission_request(teacher_id, grade_name, stream_name=None, reason=''):
        """
        Submit a permission request from a classteacher.

        Args:
            teacher_id: ID of teacher requesting permission
            grade_name: Name of the grade
            stream_name: Name of the stream (None for single classes)
            reason: Reason for requesting permission

        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            # Get grade
            grade = Grade.query.filter_by(name=grade_name).first()
            if not grade:
                return False, f"Grade '{grade_name}' not found"

            # Get stream if specified
            stream = None
            if stream_name:
                stream = Stream.query.filter_by(name=stream_name, grade_id=grade.id).first()
                if not stream:
                    return False, f"Stream '{stream_name}' not found in {grade_name}"

            # Check if request already exists
            existing_request = PermissionRequest.query.filter_by(
                teacher_id=teacher_id,
                grade_id=grade.id,
                stream_id=stream.id if stream else None,
                status='pending'
            ).first()

            if existing_request:
                class_name = f"{grade_name} {stream_name}" if stream_name else grade_name
                return False, f"You already have a pending request for {class_name}"

            # Check if permission already exists
            existing_permission = ClassTeacherPermission.query.filter_by(
                teacher_id=teacher_id,
                grade_id=grade.id,
                stream_id=stream.id if stream else None,
                is_active=True
            ).first()

            if existing_permission:
                class_name = f"{grade_name} {stream_name}" if stream_name else grade_name
                return False, f"You already have permission for {class_name}"

            # Create the request
            permission_request = PermissionRequest(
                teacher_id=teacher_id,
                grade_id=grade.id,
                stream_id=stream.id if stream else None,
                reason=reason,
                status='pending'
            )

            db.session.add(permission_request)
            db.session.commit()

            class_name = f"{grade_name} {stream_name}" if stream_name else grade_name
            return True, f"Permission request for {class_name} submitted successfully"

        except Exception as e:
            db.session.rollback()
            print(f"Error submitting permission request: {e}")
            return False, "Failed to submit permission request"

    @staticmethod
    def get_pending_requests():
        """
        Get all pending permission requests for headteacher review.

        Returns:
            List of request dictionaries
        """
        try:
            requests = db.session.query(PermissionRequest, Teacher, Grade, Stream).join(
                Teacher, PermissionRequest.teacher_id == Teacher.id
            ).join(
                Grade, PermissionRequest.grade_id == Grade.id
            ).outerjoin(
                Stream, PermissionRequest.stream_id == Stream.id
            ).filter(
                PermissionRequest.status == 'pending'
            ).all()

            request_list = []
            for req, teacher, grade, stream in requests:
                class_name = f"{grade.name} {stream.name}" if stream else grade.name
                request_list.append({
                    'id': req.id,
                    'teacher_name': teacher.full_name or teacher.username,
                    'teacher_username': teacher.username,
                    'class_name': class_name,
                    'grade_name': grade.name,
                    'stream_name': stream.name if stream else None,
                    'reason': req.reason,
                    'requested_at': req.requested_at.strftime('%Y-%m-%d %H:%M') if req.requested_at else '',
                })

            return request_list

        except Exception as e:
            print(f"Error getting pending requests: {e}")
            return []

    @staticmethod
    def process_permission_request(request_id, action, processed_by_id, admin_notes=''):
        """
        Process a permission request (approve or deny).

        Args:
            request_id: ID of the permission request
            action: 'approve' or 'deny'
            processed_by_id: ID of headteacher processing the request
            admin_notes: Optional notes from admin

        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            # Get the request
            permission_request = PermissionRequest.query.get(request_id)
            if not permission_request:
                return False, "Permission request not found"

            if permission_request.status != 'pending':
                return False, "Request has already been processed"

            # Update request status
            permission_request.status = 'approved' if action == 'approve' else 'denied'
            permission_request.processed_by = processed_by_id
            permission_request.processed_at = db.func.now()
            permission_request.admin_notes = admin_notes

            # If approved, create the permission
            if action == 'approve':
                permission = ClassTeacherPermission(
                    teacher_id=permission_request.teacher_id,
                    grade_id=permission_request.grade_id,
                    stream_id=permission_request.stream_id,
                    granted_by=processed_by_id,
                    granted_at=db.func.now(),
                    is_active=True,
                    permission_scope='full_class_admin',
                    notes=f"Approved from request: {permission_request.reason}"
                )
                db.session.add(permission)

            db.session.commit()

            # Get class name for message
            grade = Grade.query.get(permission_request.grade_id)
            stream = Stream.query.get(permission_request.stream_id) if permission_request.stream_id else None
            class_name = f"{grade.name} {stream.name}" if stream else grade.name

            action_text = "approved" if action == 'approve' else "denied"
            return True, f"Permission request for {class_name} has been {action_text}"

        except Exception as e:
            db.session.rollback()
            print(f"Error processing permission request: {e}")
            return False, "Failed to process permission request"

def check_class_access_permission(grade_name, stream_name=None):
    """
    Decorator helper function to check if current user has permission to access a class.
    Used in classteacher routes to enforce permission-based access.
    
    Args:
        grade_name: Name of the grade
        stream_name: Name of the stream (optional)
        
    Returns:
        Boolean indicating if access is allowed
    """
    # Get current user from session
    teacher_id = session.get('teacher_id')
    role = session.get('role')
    
    # Headteacher always has access
    if role == 'headteacher':
        return True
    
    # For classteachers, check permission
    if role == 'classteacher' and teacher_id:
        return PermissionService.check_classteacher_permission(teacher_id, grade_name, stream_name)
    
    return False
