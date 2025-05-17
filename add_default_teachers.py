from new_structure import create_app
from new_structure.models.user import Teacher
from new_structure.extensions import db

def add_default_teachers():
    app = create_app('development')
    with app.app_context():
        # Default teachers to add
        default_teachers = [
            {'username': 'kevin', 'password': 'password', 'role': 'classteacher'},
            {'username': 'admin', 'password': 'admin123', 'role': 'classteacher'},
            {'username': 'headteacher', 'password': 'head123', 'role': 'headteacher'},
            {'username': 'teacher', 'password': 'teach123', 'role': 'teacher'}
        ]
        
        for teacher_data in default_teachers:
            # Check if teacher already exists
            teacher = Teacher.query.filter_by(username=teacher_data['username']).first()
            if teacher:
                print(f"Teacher {teacher_data['username']} already exists")
            else:
                # Create teacher
                teacher = Teacher(
                    username=teacher_data['username'],
                    password=teacher_data['password'],
                    role=teacher_data['role']
                )
                db.session.add(teacher)
                print(f"Created teacher: {teacher_data['username']}")
        
        # Commit all changes
        db.session.commit()
        
        # List all teachers
        teachers = Teacher.query.all()
        print('\nAll teachers in database:')
        for t in teachers:
            print(f'ID: {t.id}, Username: {t.username}, Password: {t.password}, Role: {t.role}')

if __name__ == '__main__':
    add_default_teachers()
