from new_structure import create_app
from new_structure.models.user import Teacher
from new_structure.extensions import db

def add_kevin():
    app = create_app('development')
    with app.app_context():
        # Check if Kevin already exists
        kevin = Teacher.query.filter_by(username='kevin').first()
        if kevin:
            print(f"Kevin already exists: ID: {kevin.id}, Username: {kevin.username}, Password: {kevin.password}, Role: {kevin.role}")
        else:
            # Create Kevin
            kevin = Teacher(username='kevin', password='password', role='classteacher')
            db.session.add(kevin)
            db.session.commit()
            print(f"Created Kevin: ID: {kevin.id}, Username: {kevin.username}, Password: {kevin.password}, Role: {kevin.role}")
        
        # List all teachers
        teachers = Teacher.query.all()
        print('\nAll teachers in database:')
        for t in teachers:
            print(f'ID: {t.id}, Username: {t.username}, Password: {t.password}, Role: {t.role}')

if __name__ == '__main__':
    add_kevin()
