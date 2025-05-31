"""
Add a temporary route to add Kevin user.
Add this to your Flask app temporarily.
"""

from flask import Blueprint

# Create a temporary blueprint
temp_bp = Blueprint('temp', __name__)

@temp_bp.route('/add_kevin')
def add_kevin():
    """Add Kevin user to the database."""
    try:
        from .extensions import db
        from .models.user import Teacher
        
        # Check if Kevin exists
        kevin = Teacher.query.filter_by(username='kevin').first()
        
        if kevin:
            return f"Kevin already exists: {kevin.username}, role: {kevin.role}"
        
        # Add Kevin
        kevin = Teacher(
            username='kevin',
            password='kev123',
            role='classteacher',
            full_name='Kevin Teacher',
            employee_id='EMP002',
            is_active=True
        )
        
        db.session.add(kevin)
        db.session.commit()
        
        return "✅ Kevin added successfully! You can now login with kevin/kev123"
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

@temp_bp.route('/check_users')
def check_users():
    """Check all users in the database."""
    try:
        from .models.user import Teacher
        
        teachers = Teacher.query.all()
        
        result = f"<h2>Users in Database ({len(teachers)} total):</h2><ul>"
        
        for teacher in teachers:
            result += f"<li><strong>{teacher.username}</strong> - Password: {teacher.password} - Role: {teacher.role}</li>"
        
        result += "</ul>"
        
        # Check for Kevin specifically
        kevin = Teacher.query.filter_by(username='kevin').first()
        if kevin:
            result += f"<p>✅ <strong>Kevin found!</strong> Username: {kevin.username}, Password: {kevin.password}</p>"
        else:
            result += f"<p>❌ <strong>Kevin NOT found</strong></p>"
            result += f'<p><a href="/add_kevin">Click here to add Kevin</a></p>'
        
        return result
        
    except Exception as e:
        return f"❌ Error: {str(e)}"
