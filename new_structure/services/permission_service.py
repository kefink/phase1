"""
Permission management service for the delegation-based access control system.
Handles permission granting, revoking, and checking for classteachers.
"""
from ..models import ClassTeacherPermission, PermissionRequest, Teacher, Grade, Stream
from ..extensions import db
import time
from sqlalchemy.exc import OperationalError
from flask import session

class PermissionService:
    """Service class for managing classteacher permissions."""
    @staticmethod
    def check_class_access(user_id, grade_id, stream_id=None):
        """Check access using numeric identifiers (used by unified authorization layer).

        This method differs from check_classteacher_permission which accepts grade/stream names.
        Here we operate directly on ids to avoid extra lookups when already resolved.

        Access Rules:
            - headteacher / admin / superadmin: always True
            - classteacher: must possess active ClassTeacherPermission record (grade + optional stream)
            - teacher: currently treated similar to classteacher for read/write marks if permission exists
              (future refinement may differentiate teacher vs classteacher scopes)
            - others: False

        Args:
            user_id: int – teacher id from session
            grade_id: int – grade primary key
            stream_id: Optional[int] – stream primary key or None for single-class grades

        Returns:
            bool: True if user has class scope access
        """
        try:
            if not user_id or not grade_id:
                return False

            # Resolve role once (avoid importing auth_service at module import time to prevent circulars)
            from flask import session as _session  # lazy import; tests may patch session
            role = _session.get('role') if _session else None

            if role in ('headteacher', 'admin', 'superadmin'):
                return True

            if role in ('classteacher', 'teacher'):
                # Primary: explicit permission record
                if ClassTeacherPermission.has_permission(
                    teacher_id=user_id,
                    grade_id=grade_id,
                    stream_id=stream_id
                ):
                    return True

                # Fallback A: direct stream assignment on Teacher record
                try:
                    teacher = Teacher.query.get(user_id)
                except Exception:
                    teacher = None
                if teacher and teacher.stream_id:
                    try:
                        # Match exact stream when provided
                        if stream_id and int(teacher.stream_id) == int(stream_id):
                            return True
                    except Exception:
                        pass
                    # Fallback B: if no stream specified (single-stream context), allow when grade matches
                    if stream_id is None:
                        try:
                            t_stream = Stream.query.get(teacher.stream_id)
                            if t_stream and int(t_stream.grade_id) == int(grade_id):
                                return True
                        except Exception:
                            pass

                # Fallback C: honor role-based class teacher assignments for classteachers
                if role == 'classteacher':
                    try:
                        from ..services.role_based_data_service import RoleBasedDataService as _RBDS
                        summary = _RBDS.get_teacher_assignments_summary(user_id, 'classteacher')
                        if summary and not summary.get('error'):
                            for a in summary.get('class_teacher_assignments', []) or []:
                                if int(a.get('grade_id') or 0) == int(grade_id):
                                    if stream_id is None or int(a.get('stream_id') or 0) == int(stream_id):
                                        return True
                    except Exception:
                        pass

                # No explicit permission and no recognized assignment
                return False
            return False
        except Exception as e:  # pragma: no cover - defensive
            print(f"Error in check_class_access: {e}")
            return False
    
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

            # Resolve grade/stream names directly to avoid relying on ORM relationships
            try:
                _Grade = Grade
                _Stream = Stream
            except Exception:
                _Grade = _Stream = None

            for perm in permissions:
                try:
                    grade_name = None
                    stream_name = None
                    if _Grade and perm.grade_id:
                        try:
                            g = _Grade.query.get(perm.grade_id)
                            grade_name = getattr(g, 'name', None)
                        except Exception:
                            pass
                    if _Stream and perm.stream_id:
                        try:
                            s = _Stream.query.get(perm.stream_id)
                            stream_name = getattr(s, 'name', None)
                        except Exception:
                            pass

                    display = grade_name or str(perm.grade_id)
                    if stream_name:
                        display = f"{display} {stream_name}"

                    class_info = {
                        'grade_name': grade_name,
                        'grade_id': perm.grade_id,
                        'stream_name': stream_name,
                        'stream_id': perm.stream_id,
                        'granted_at': perm.granted_at,
                        'permission_id': perm.id,
                        'display_name': display
                    }
                    classes.append(class_info)
                except Exception:
                    # Skip malformed permission row gracefully
                    continue
            
            return classes
            
        except Exception as e:
            print(f"Error getting teacher classes: {e}")
            return []
    
    @staticmethod
    def grant_permission(teacher_id, grade_name, stream_name, granted_by_id, notes=None):
        """
        Grant permission to a teacher for a specific class/stream with 1-hour expiration.
        
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
            
            # Grant permission with 1-hour expiration
            from datetime import datetime, timedelta
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            permission = ClassTeacherPermission.grant_permission(
                teacher_id=teacher_id,
                grade_id=grade.id,
                stream_id=stream.id if stream else None,
                granted_by_id=granted_by_id,
                notes=f"{notes} (1-hour access)" if notes else "1-hour access granted",
                expires_at=expires_at,
                is_permanent=False
            )
            
            if permission:
                class_name = f"{grade_name} {stream_name}" if stream_name else grade_name
                return True, f"Permission granted successfully for {class_name} (expires in 1 hour)"
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

            # Ensure runtime schema for ClassTeacherPermission.revoked_at is present (summary uses status/expiry)
            try:
                # no-op call that triggers potential self-heal
                ClassTeacherPermission._ensure_revoked_at_column()
            except Exception:
                pass

            # Get current permissions
            current_permissions = ClassTeacherPermission.get_all_permissions_summary()

            # Ensure core columns for permission_requests exist, then fetch pending
            try:
                PermissionRequest.ensure_core_columns()
            except Exception:
                pass

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
        def _is_table_changed_error(err) -> bool:
            try:
                if isinstance(err, OperationalError):
                    msg = str(err)
                    return ('Table definition has changed' in msg) or (' 1412' in msg) or ('(1412,' in msg)
            except Exception:
                pass
            # Also match by message string just in case
            try:
                msg = str(err)
                return 'Table definition has changed' in msg
            except Exception:
                return False

        for attempt in range(2):
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

                # Ensure columns exist before querying/creating
                try:
                    PermissionRequest.ensure_core_columns()
                except Exception:
                    pass

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
                if _is_table_changed_error(e) and attempt == 0:
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
                    try:
                        PermissionRequest.ensure_core_columns()
                    except Exception:
                        pass
                    # Small delay to let MySQL finalize table change and invalidate prepared statements
                    time.sleep(0.2)
                    continue
                try:
                    db.session.rollback()
                except Exception:
                    pass
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
            # Ensure columns used by joins exist
            try:
                PermissionRequest.ensure_core_columns()
            except Exception:
                pass

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
            # Ensure columns exist prior to processing
            try:
                PermissionRequest.ensure_core_columns()
            except Exception:
                pass

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

            # If approved, create the permission with 1-hour expiration
            if action == 'approve':
                from datetime import datetime, timedelta
                expires_at = datetime.utcnow() + timedelta(hours=1)
                
                permission = ClassTeacherPermission(
                    teacher_id=permission_request.teacher_id,
                    grade_id=permission_request.grade_id,
                    stream_id=permission_request.stream_id,
                    granted_by=processed_by_id,
                    granted_at=db.func.now(),
                    expires_at=expires_at,
                    is_active=True,
                    is_permanent=False,  # Explicitly set as temporary
                    permission_scope='full_class_admin',
                    notes=f"Approved from request: {permission_request.reason} (1-hour access)"
                )
                db.session.add(permission)

            db.session.commit()

            # Get class name for message
            grade = Grade.query.get(permission_request.grade_id)
            stream = Stream.query.get(permission_request.stream_id) if permission_request.stream_id else None
            class_name = f"{grade.name} {stream.name}" if stream else grade.name

            action_text = "approved" if action == 'approve' else "denied"
            if action == 'approve':
                return True, f"Permission request for {class_name} has been {action_text} (1-hour access granted)"
            else:
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
