"""
Authentication services for the Hillview School Management System.
"""
from ..models import Teacher

def authenticate_teacher(username, password, role):
    """
    Authenticate a teacher with the given credentials.
    
    Args:
        username: The teacher's username
        password: The teacher's password
        role: The teacher's role (headteacher, teacher, classteacher)
        
    Returns:
        Teacher object if authentication is successful, None otherwise
    """
    return Teacher.query.filter_by(username=username, password=password, role=role).first()

def get_teacher_by_id(teacher_id):
    """
    Get a teacher by ID.
    
    Args:
        teacher_id: The teacher's ID
        
    Returns:
        Teacher object if found, None otherwise
    """
    return Teacher.query.get(teacher_id)

def is_authenticated(session):
    """
    Check if a user is authenticated based on session data.
    
    Args:
        session: The Flask session object
        
    Returns:
        Boolean indicating if the user is authenticated
    """
    return 'teacher_id' in session

def get_role(session):
    """
    Get the role of the authenticated user.
    
    Args:
        session: The Flask session object
        
    Returns:
        String representing the user's role, or None if not authenticated
    """
    return session.get('role')

def logout(session):
    """
    Log out the current user by clearing the session.
    
    Args:
        session: The Flask session object
    """
    session.clear()