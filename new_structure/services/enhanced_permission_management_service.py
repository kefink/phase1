"""
Enhanced Permission Management Service with Direct Granting and Automatic Expiration.
Provides comprehensive permission management for headteachers with time-based controls.
"""

from datetime import datetime, timedelta
from ..models.permission import ClassTeacherPermission, PermissionRequest
from ..models import Teacher, Grade, Stream
from ..extensions import db
from typing import Optional, List, Dict, Any


class EnhancedPermissionManagementService:
    """
    Enhanced service for managing permissions with direct granting and automatic expiration.
    """
    
    # Predefined duration options for permissions
    DURATION_OPTIONS = {
        '1_day': {'days': 1, 'label': '1 Day'},
        '3_days': {'days': 3, 'label': '3 Days'},
        '1_week': {'days': 7, 'label': '1 Week'},
        '2_weeks': {'days': 14, 'label': '2 Weeks'},
        '1_month': {'days': 30, 'label': '1 Month'},
        '3_months': {'days': 90, 'label': '3 Months'},
        '6_months': {'days': 180, 'label': '6 Months'},
        '1_year': {'days': 365, 'label': '1 Year'},
        'permanent': {'days': None, 'label': 'Permanent'}
    }
    
    @classmethod
    def grant_direct_permission(cls, teacher_id: int, grade_id: int, stream_id: Optional[int],
                               granted_by_id: int, duration_key: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Grant permission directly to a teacher with specified duration.
        
        Args:
            teacher_id: ID of teacher receiving permission
            grade_id: ID of the grade
            stream_id: ID of the stream (None for single classes)
            granted_by_id: ID of headteacher granting permission
            duration_key: Key from DURATION_OPTIONS
            notes: Optional notes about the permission
            
        Returns:
            Dictionary with success status and details
        """
        try:
            # Validate inputs
            teacher = Teacher.query.get(teacher_id)
            grade = Grade.query.get(grade_id)
            granted_by = Teacher.query.get(granted_by_id)
            
            if not teacher:
                return {'success': False, 'message': 'Teacher not found'}
            if not grade:
                return {'success': False, 'message': 'Grade not found'}
            if not granted_by:
                return {'success': False, 'message': 'Granting teacher not found'}
            
            if stream_id:
                stream = Stream.query.get(stream_id)
                if not stream:
                    return {'success': False, 'message': 'Stream not found'}
            
            # Calculate expiration date
            expires_at = None
            is_permanent = False
            
            if duration_key in cls.DURATION_OPTIONS:
                duration_info = cls.DURATION_OPTIONS[duration_key]
                if duration_info['days'] is None:
                    is_permanent = True
                else:
                    expires_at = datetime.utcnow() + timedelta(days=duration_info['days'])
            else:
                return {'success': False, 'message': 'Invalid duration specified'}
            
            # Check if permission already exists
            existing = ClassTeacherPermission.query.filter_by(
                teacher_id=teacher_id,
                grade_id=grade_id,
                stream_id=stream_id,
                is_active=True
            ).first()
            
            if existing:
                # Update existing permission
                existing.expires_at = expires_at
                existing.is_permanent = is_permanent
                existing.auto_granted = True
                existing.granted_by = granted_by_id
                existing.granted_at = datetime.utcnow()
                if notes:
                    existing.notes = notes
                
                db.session.commit()
                
                action = 'updated'
                permission = existing
            else:
                # Create new permission
                permission = ClassTeacherPermission.grant_permission(
                    teacher_id=teacher_id,
                    grade_id=grade_id,
                    stream_id=stream_id,
                    granted_by_id=granted_by_id,
                    notes=notes,
                    expires_at=expires_at,
                    is_permanent=is_permanent,
                    auto_granted=True
                )
                
                if not permission:
                    return {'success': False, 'message': 'Failed to create permission'}
                
                action = 'granted'
            
            # Format response
            stream_info = f" Stream {permission.stream.name}" if permission.stream else ""
            duration_label = cls.DURATION_OPTIONS[duration_key]['label']
            
            return {
                'success': True,
                'message': f'Permission {action} successfully for {teacher.full_name or teacher.username} '
                          f'to manage {grade.name}{stream_info} for {duration_label}',
                'permission_id': permission.id,
                'expires_at': expires_at.isoformat() if expires_at else None,
                'is_permanent': is_permanent,
                'teacher_name': teacher.full_name or teacher.username,
                'class_info': f"{grade.name}{stream_info}"
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Error granting permission: {str(e)}'}
    
    @classmethod
    def bulk_grant_permissions(cls, teacher_id: int, class_assignments: List[Dict], 
                              granted_by_id: int, duration_key: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Grant multiple permissions to a teacher at once.
        
        Args:
            teacher_id: ID of teacher receiving permissions
            class_assignments: List of {'grade_id': int, 'stream_id': int|None} dicts
            granted_by_id: ID of headteacher granting permissions
            duration_key: Key from DURATION_OPTIONS
            notes: Optional notes about the permissions
            
        Returns:
            Dictionary with success status and details
        """
        try:
            results = []
            successful_grants = 0
            
            for assignment in class_assignments:
                result = cls.grant_direct_permission(
                    teacher_id=teacher_id,
                    grade_id=assignment['grade_id'],
                    stream_id=assignment.get('stream_id'),
                    granted_by_id=granted_by_id,
                    duration_key=duration_key,
                    notes=notes
                )
                
                results.append(result)
                if result['success']:
                    successful_grants += 1
            
            return {
                'success': successful_grants > 0,
                'message': f'Successfully granted {successful_grants} out of {len(class_assignments)} permissions',
                'successful_grants': successful_grants,
                'total_attempts': len(class_assignments),
                'results': results
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error in bulk grant: {str(e)}'}
    
    @classmethod
    def get_expiring_permissions(cls, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get permissions that will expire within specified days.
        
        Args:
            days_ahead: Number of days to look ahead for expiring permissions
            
        Returns:
            List of permission dictionaries
        """
        try:
            cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
            
            expiring_permissions = ClassTeacherPermission.query.filter(
                ClassTeacherPermission.is_active == True,
                ClassTeacherPermission.is_permanent == False,
                ClassTeacherPermission.expires_at != None,
                ClassTeacherPermission.expires_at <= cutoff_date,
                ClassTeacherPermission.expires_at > datetime.utcnow()
            ).all()
            
            results = []
            for perm in expiring_permissions:
                stream_info = f" Stream {perm.stream.name}" if perm.stream else ""
                results.append({
                    'id': perm.id,
                    'teacher_name': perm.teacher.full_name or perm.teacher.username,
                    'teacher_id': perm.teacher_id,
                    'class_info': f"{perm.grade.name}{stream_info}",
                    'expires_at': perm.expires_at,
                    'days_until_expiry': perm.days_until_expiry,
                    'status': perm.status,
                    'granted_by_name': perm.granted_by_teacher.full_name or perm.granted_by_teacher.username
                })
            
            return results
            
        except Exception as e:
            print(f"Error getting expiring permissions: {e}")
            return []
    
    @classmethod
    def extend_permission(cls, permission_id: int, duration_key: str, extended_by_id: int) -> Dict[str, Any]:
        """
        Extend an existing permission's expiration date.
        
        Args:
            permission_id: ID of the permission to extend
            duration_key: Key from DURATION_OPTIONS for additional time
            extended_by_id: ID of headteacher extending the permission
            
        Returns:
            Dictionary with success status and details
        """
        try:
            permission = ClassTeacherPermission.query.get(permission_id)
            if not permission:
                return {'success': False, 'message': 'Permission not found'}
            
            if not permission.is_active:
                return {'success': False, 'message': 'Permission is not active'}
            
            # Calculate new expiration date
            if duration_key == 'permanent':
                permission.is_permanent = True
                permission.expires_at = None
                new_expiry_info = "Permanent"
            else:
                duration_info = cls.DURATION_OPTIONS.get(duration_key)
                if not duration_info or duration_info['days'] is None:
                    return {'success': False, 'message': 'Invalid duration specified'}
                
                # Extend from current expiry date or now, whichever is later
                base_date = max(permission.expires_at or datetime.utcnow(), datetime.utcnow())
                permission.expires_at = base_date + timedelta(days=duration_info['days'])
                permission.is_permanent = False
                new_expiry_info = permission.expires_at.strftime('%Y-%m-%d %H:%M')
            
            # Update metadata
            permission.granted_by = extended_by_id
            permission.granted_at = datetime.utcnow()
            
            db.session.commit()
            
            stream_info = f" Stream {permission.stream.name}" if permission.stream else ""
            teacher_name = permission.teacher.full_name or permission.teacher.username
            
            return {
                'success': True,
                'message': f'Permission extended for {teacher_name} to manage '
                          f'{permission.grade.name}{stream_info} until {new_expiry_info}',
                'permission_id': permission.id,
                'new_expires_at': permission.expires_at.isoformat() if permission.expires_at else None,
                'is_permanent': permission.is_permanent
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Error extending permission: {str(e)}'}
    
    @classmethod
    def get_permission_statistics(cls) -> Dict[str, Any]:
        """
        Get comprehensive statistics about permissions.
        
        Returns:
            Dictionary with permission statistics
        """
        try:
            # Expire old permissions first
            ClassTeacherPermission.expire_permissions()
            
            total_active = ClassTeacherPermission.query.filter_by(is_active=True).count()
            permanent_count = ClassTeacherPermission.query.filter_by(is_active=True, is_permanent=True).count()
            temporary_count = total_active - permanent_count
            
            # Get expiring soon (within 7 days)
            expiring_soon = len(cls.get_expiring_permissions(7))
            
            # Get auto-granted vs request-approved
            auto_granted = ClassTeacherPermission.query.filter_by(is_active=True, auto_granted=True).count()
            request_approved = total_active - auto_granted
            
            return {
                'total_active_permissions': total_active,
                'permanent_permissions': permanent_count,
                'temporary_permissions': temporary_count,
                'expiring_soon': expiring_soon,
                'auto_granted': auto_granted,
                'request_approved': request_approved
            }
            
        except Exception as e:
            print(f"Error getting permission statistics: {e}")
            return {
                'total_active_permissions': 0,
                'permanent_permissions': 0,
                'temporary_permissions': 0,
                'expiring_soon': 0,
                'auto_granted': 0,
                'request_approved': 0
            }
