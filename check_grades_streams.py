from new_structure import create_app
from new_structure.models import Grade, Stream

app = create_app()

with app.app_context():
    grades = Grade.query.all()
    print(f'Total grades: {len(grades)}')

    if grades:
        print("\nGrades and their streams:")
        for grade in grades:
            streams = Stream.query.filter_by(grade_id=grade.id).all()
            print(f'Grade: {grade.level} (ID: {grade.id}), Streams: {len(streams)}')

            if streams:
                for stream in streams:
                    print(f'  - Stream: {stream.name} (ID: {stream.id})')
            else:
                print("  - No streams for this grade")
    else:
        print("No grades found in the database.")
