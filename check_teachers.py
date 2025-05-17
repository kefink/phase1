from new_structure import create_app
from new_structure.models.user import Teacher

def list_teachers():
    app = create_app('development')
    with app.app_context():
        teachers = Teacher.query.all()
        print('All teachers in database:')
        for t in teachers:
            print(f'ID: {t.id}, Username: {t.username}, Password: {t.password}, Role: {t.role}')

if __name__ == '__main__':
    list_teachers()
