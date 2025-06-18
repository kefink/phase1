"""
Insecure Direct Object References (IDOR) Protection Module
Comprehensive protection against IDOR vulnerabilities.
"""

import logging
from functools import wraps
from flask import session, request, abort, current_app
try:
    from ..services.auth_service import get_role
except ImportError:
    try:
        from services.auth_service import get_role
    except ImportError:
        def get_role(session):
            return session.get('role', 'guest')

class IDORProtection:
    """Comprehensive IDOR protection."""
    
    # Object type to ownership field mapping
    OWNERSHIP_MAPPING = {
        'student': 'teacher_id',  # Students belong to teachers/classteachers
        'mark': 'teacher_id',     # Marks belong to the teacher who entered them
        'report': 'teacher_id',   # Reports belong to the teacher who generated them
        'assignment': 'teacher_id',  # Assignments belong to teachers
        'parent': 'id',           # Parents own their own records
        'teacher': 'id',          # Teachers own their own records
        'grade': None,            # Grades are system-wide (admin only)
        'stream': None,           # Streams are system-wide (admin only)
        'subject': None,          # Subjects are system-wide (admin only)
        'term': None,             # Terms are system-wide (admin only)
        'assessment_type': None   # Assessment types are system-wide (admin only)
    }
    
    # Object type to access level mapping
    ACCESS_LEVELS = {
        'student': {
            'read': ['teacher', 'classteacher', 'headteacher', 'admin'],
            'write': ['classteacher', 'headteacher', 'admin'],
            'delete': ['headteacher', 'admin']
        },
        'mark': {
            'read': ['teacher', 'classteacher', 'headteacher', 'admin'],
            'write': ['teacher', 'classteacher', 'headteacher', 'admin'],
            'delete': ['headteacher', 'admin']
        },
        'report': {
            'read': ['teacher', 'classteacher', 'headteacher', 'admin', 'parent'],
            'write': ['classteacher', 'headteacher', 'admin'],
            'delete': ['headteacher', 'admin']
        },
        'assignment': {
            'read': ['teacher', 'classteacher', 'headteacher', 'admin'],
            'write': ['teacher', 'classteacher', 'headteacher', 'admin'],
            'delete': ['headteacher', 'admin']
        },
        'parent': {
            'read': ['parent', 'headteacher', 'admin'],
            'write': ['parent', 'headteacher', 'admin'],
            'delete': ['headteacher', 'admin']
        },
        'teacher': {
            'read': ['teacher', 'headteacher', 'admin'],
            'write': ['teacher', 'headteacher', 'admin'],
            'delete': ['admin']
        }
    }
    
    @classmethod
    def check_object_access(cls, user_id, user_role, object_type, object_id, action='read'):
        """
        Check if user has access to specific object.
        
        Args:
            user_id: Current user's ID
            user_role: Current user's role
            object_type: Type of object being accessed
            object_id: ID of the object
            action: Action being performed (read, write, delete)
            
        Returns:
            bool: True if access granted
        """
        # Check if object type is valid
        if object_type not in cls.ACCESS_LEVELS:
            logging.warning(f"Unknown object type: {object_type}")
            return False
        
        # Check role-based access
        allowed_roles = cls.ACCESS_LEVELS[object_type].get(action, [])
        if user_role not in allowed_roles:
            logging.warning(f"Role {user_role} not allowed {action} access to {object_type}")
            return False
        
        # Check ownership if applicable
        ownership_field = cls.OWNERSHIP_MAPPING.get(object_type)
        if ownership_field:
            return cls.check_object_ownership(user_id, user_role, object_type, object_id, ownership_field)
        
        # If no ownership check needed, role check is sufficient
        return True
    
    @classmethod
    def check_object_ownership(cls, user_id, user_role, object_type, object_id, ownership_field):
        """
        Check object ownership.
        
        Args:
            user_id: Current user's ID
            user_role: Current user's role
            object_type: Type of object
            object_id: ID of the object
            ownership_field: Field that contains owner ID
            
        Returns:
            bool: True if access granted
        """
        # Admin and headteacher have universal access
        if user_role in ['admin', 'headteacher']:
            return True
        
        try:
            # Get the object from database
            object_data = cls.get_object_data(object_type, object_id)
            if not object_data:
                logging.warning(f"Object {object_type}:{object_id} not found")
                return False
            
            # Check ownership
            owner_id = object_data.get(ownership_field)
            if str(owner_id) == str(user_id):
                return True
            
            # Special cases for different object types
            if object_type == 'student':
                # Teachers can access students in their assigned classes
                return cls.check_student_class_access(user_id, object_id)
            elif object_type == 'report':
                # Parents can access their children's reports
                if user_role == 'parent':
                    return cls.check_parent_child_access(user_id, object_data.get('student_id'))
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking object ownership: {e}")
            return False
    
    @classmethod
    def get_object_data(cls, object_type, object_id):
        """
        Get object data from database.
        
        Args:
            object_type: Type of object
            object_id: ID of the object
            
        Returns:
            dict: Object data or None
        """
        try:
            try:
                from ..models import Student, Mark, Teacher, Grade, Stream, Subject
                from ..models.parent import Parent
                from ..models.report import Report
            except ImportError:
                try:
                    from models import Student, Mark, Teacher, Grade, Stream, Subject
                    from models.parent import Parent
                    from models.report import Report
                except ImportError:
                    # Mock models for testing
                    class MockModel:
                        @classmethod
                        def query(cls):
                            return cls
                        @classmethod
                        def get(cls, id):
                            return None
                    Student = Mark = Teacher = Grade = Stream = Subject = Parent = Report = MockModel
            
            model_mapping = {
                'student': Student,
                'mark': Mark,
                'teacher': Teacher,
                'parent': Parent,
                'report': Report,
                'grade': Grade,
                'stream': Stream,
                'subject': Subject
            }
            
            model = model_mapping.get(object_type)
            if not model:
                return None
            
            obj = model.query.get(object_id)
            if not obj:
                return None
            
            # Convert to dict
            return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}
            
        except Exception as e:
            logging.error(f"Error getting object data: {e}")
            return None
    
    @classmethod
    def check_student_class_access(cls, teacher_id, student_id):
        """
        Check if teacher has access to student through class assignment.
        
        Args:
            teacher_id: Teacher's ID
            student_id: Student's ID
            
        Returns:
            bool: True if access granted
        """
        try:
            try:
                from ..services.permission_service import PermissionService
                from ..models import Student
            except ImportError:
                try:
                    from services.permission_service import PermissionService
                    from models import Student
                except ImportError:
                    class PermissionService:
                        @staticmethod
                        def check_class_access(user_id, grade_id, stream_id):
                            return True
                    class Student:
                        @classmethod
                        def query(cls):
                            return cls
                        @classmethod
                        def get(cls, id):
                            return None
            
            student = Student.query.get(student_id)
            if not student:
                return False
            
            # Check if teacher has permission for this student's class
            return PermissionService.check_class_access(
                teacher_id, student.grade_id, student.stream_id
            )
            
        except Exception as e:
            logging.error(f"Error checking student class access: {e}")
            return False
    
    @classmethod
    def check_parent_child_access(cls, parent_id, student_id):
        """
        Check if parent has access to student (their child).
        
        Args:
            parent_id: Parent's ID
            student_id: Student's ID
            
        Returns:
            bool: True if access granted
        """
        try:
            try:
                from ..models.parent import ParentStudent
            except ImportError:
                try:
                    from models.parent import ParentStudent
                except ImportError:
                    class ParentStudent:
                        @classmethod
                        def query(cls):
                            return cls
                        @classmethod
                        def filter_by(cls, **kwargs):
                            return cls
                        @classmethod
                        def first(cls):
                            return None
            
            link = ParentStudent.query.filter_by(
                parent_id=parent_id,
                student_id=student_id
            ).first()
            
            return link is not None
            
        except Exception as e:
            logging.error(f"Error checking parent-child access: {e}")
            return False
    
    @classmethod
    def get_accessible_objects(cls, user_id, user_role, object_type, action='read'):
        """
        Get list of object IDs that user can access.
        
        Args:
            user_id: Current user's ID
            user_role: Current user's role
            object_type: Type of objects
            action: Action being performed
            
        Returns:
            list: List of accessible object IDs
        """
        # Check role-based access first
        allowed_roles = cls.ACCESS_LEVELS.get(object_type, {}).get(action, [])
        if user_role not in allowed_roles:
            return []
        
        # Admin and headteacher have universal access
        if user_role in ['admin', 'headteacher']:
            return cls.get_all_object_ids(object_type)
        
        # Get objects based on ownership/permission
        ownership_field = cls.OWNERSHIP_MAPPING.get(object_type)
        if ownership_field:
            return cls.get_owned_object_ids(user_id, object_type, ownership_field)
        else:
            return cls.get_all_object_ids(object_type)
    
    @classmethod
    def get_all_object_ids(cls, object_type):
        """
        Get all object IDs of given type.
        
        Args:
            object_type: Type of objects
            
        Returns:
            list: List of all object IDs
        """
        try:
            from ..models import Student, Mark, Teacher, Grade, Stream, Subject
            from ..models.parent import Parent
            from ..models.report import Report
            
            model_mapping = {
                'student': Student,
                'mark': Mark,
                'teacher': Teacher,
                'parent': Parent,
                'report': Report,
                'grade': Grade,
                'stream': Stream,
                'subject': Subject
            }
            
            model = model_mapping.get(object_type)
            if not model:
                return []
            
            return [obj.id for obj in model.query.all()]
            
        except Exception as e:
            logging.error(f"Error getting all object IDs: {e}")
            return []
    
    @classmethod
    def get_owned_object_ids(cls, user_id, object_type, ownership_field):
        """
        Get object IDs owned by user.
        
        Args:
            user_id: User's ID
            object_type: Type of objects
            ownership_field: Field containing owner ID
            
        Returns:
            list: List of owned object IDs
        """
        try:
            from ..models import Student, Mark, Teacher
            from ..models.parent import Parent
            from ..models.report import Report
            
            model_mapping = {
                'student': Student,
                'mark': Mark,
                'teacher': Teacher,
                'parent': Parent,
                'report': Report
            }
            
            model = model_mapping.get(object_type)
            if not model:
                return []
            
            # Query objects owned by user
            filter_condition = {ownership_field: user_id}
            objects = model.query.filter_by(**filter_condition).all()
            
            return [obj.id for obj in objects]
            
        except Exception as e:
            logging.error(f"Error getting owned object IDs: {e}")
            return []

def protect_object_access(object_type, action='read', id_param='id'):
    """
    Decorator to protect object access from IDOR attacks.
    
    Args:
        object_type: Type of object being accessed
        action: Action being performed (read, write, delete)
        id_param: Parameter name containing object ID
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('teacher_id') or session.get('parent_id')
            user_role = get_role(session)
            
            if not user_id or not user_role:
                abort(401, "Authentication required")
            
            # Get object ID from various sources
            object_id = None
            
            # Try kwargs first
            if id_param in kwargs:
                object_id = kwargs[id_param]
            # Try URL parameters
            elif id_param in request.args:
                object_id = request.args.get(id_param)
            # Try form data
            elif id_param in request.form:
                object_id = request.form.get(id_param)
            # Try JSON data
            elif request.is_json and id_param in request.json:
                object_id = request.json.get(id_param)
            
            if not object_id:
                abort(400, f"Missing {id_param} parameter")
            
            # Check access
            if not IDORProtection.check_object_access(user_id, user_role, object_type, object_id, action):
                logging.warning(f"IDOR attack blocked: User {user_id} ({user_role}) attempted {action} on {object_type}:{object_id}")
                abort(403, "Access denied")
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def filter_accessible_objects(object_type, action='read'):
    """
    Decorator to filter objects to only those accessible by current user.
    
    Args:
        object_type: Type of objects
        action: Action being performed
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('teacher_id') or session.get('parent_id')
            user_role = get_role(session)
            
            if not user_id or not user_role:
                abort(401, "Authentication required")
            
            # Get accessible object IDs
            accessible_ids = IDORProtection.get_accessible_objects(user_id, user_role, object_type, action)
            
            # Add to kwargs for use in route function
            kwargs['accessible_object_ids'] = accessible_ids
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
