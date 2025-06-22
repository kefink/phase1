"""
User factory for creating test data in Hillview School Management System.
"""

from new_structure.extensions import db
from new_structure.models.user import Teacher

def create_test_users():
    """Create test users for all roles."""
    
    # Test Headteacher
    headteacher = Teacher(
        username='test_headteacher',
        password='test123',
        role='headteacher'
    )
    
    # Test Classteacher
    classteacher = Teacher(
        username='test_classteacher',
        password='test123',
        role='classteacher'
    )
    
    # Test Teacher
    teacher = Teacher(
        username='test_teacher',
        password='test123',
        role='teacher'
    )
    
    # Add enhanced fields if they exist
    for user in [headteacher, classteacher, teacher]:
        # Check if the attribute exists and is settable
        try:
            if hasattr(Teacher, 'full_name') and hasattr(user, 'full_name'):
                user.full_name = f'Test {user.role.title()}'
        except (AttributeError, TypeError):
            pass

        try:
            if hasattr(Teacher, 'employee_id') and hasattr(user, 'employee_id'):
                user.employee_id = f'TEST_{user.role.upper()}'
        except (AttributeError, TypeError):
            pass

        try:
            if hasattr(Teacher, 'is_active') and hasattr(user, 'is_active'):
                user.is_active = True
        except (AttributeError, TypeError):
            pass
    
    # Add to database
    db.session.add_all([headteacher, classteacher, teacher])
    db.session.commit()
    
    return {
        'headteacher': headteacher,
        'classteacher': classteacher,
        'teacher': teacher
    }
