from new_structure import create_app
from new_structure.models import Grade

app = create_app()

with app.app_context():
    grades = Grade.query.all()
    for grade in grades:
        print(f'Grade ID: {grade.id}, Level: {grade.level}')
