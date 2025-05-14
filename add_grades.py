from new_structure import create_app
from new_structure.models import Grade, Stream
from new_structure.extensions import db

app = create_app()

with app.app_context():
    # Check existing grades
    existing_grades = Grade.query.all()
    print(f'Existing grades: {len(existing_grades)}')
    for grade in existing_grades:
        print(f"  - {grade.level} (ID: {grade.id})")
    
    # Define grades for each education level
    lower_primary_grades = ["Grade 1", "Grade 2", "Grade 3"]
    upper_primary_grades = ["Grade 4", "Grade 5", "Grade 6"]
    junior_secondary_grades = ["Grade 7", "Grade 8", "Grade 9"]
    
    # Add lower primary grades
    for grade_level in lower_primary_grades:
        # Check if grade already exists
        if not Grade.query.filter_by(level=grade_level).first():
            grade = Grade(level=grade_level)
            db.session.add(grade)
            print(f"Added grade: {grade_level}")
    
    # Add upper primary grades
    for grade_level in upper_primary_grades:
        # Check if grade already exists
        if not Grade.query.filter_by(level=grade_level).first():
            grade = Grade(level=grade_level)
            db.session.add(grade)
            print(f"Added grade: {grade_level}")
    
    # Add junior secondary grades (if needed)
    for grade_level in junior_secondary_grades:
        # Check if grade already exists
        if not Grade.query.filter_by(level=grade_level).first():
            grade = Grade(level=grade_level)
            db.session.add(grade)
            print(f"Added grade: {grade_level}")
    
    # Commit changes
    db.session.commit()
    
    # Add streams to each grade
    all_grades = Grade.query.all()
    
    # Add streams A and B to each grade
    for grade in all_grades:
        # Check if grade already has streams
        existing_streams = Stream.query.filter_by(grade_id=grade.id).all()
        if not existing_streams:
            # Add streams A and B
            for stream_name in ["A", "B"]:
                stream = Stream(name=stream_name, grade_id=grade.id)
                db.session.add(stream)
                print(f"Added stream {stream_name} to {grade.level}")
    
    # Commit changes
    db.session.commit()
    
    # Verify grades and streams after adding
    all_grades = Grade.query.all()
    print(f'\nTotal grades after adding: {len(all_grades)}')
    
    for grade in all_grades:
        streams = Stream.query.filter_by(grade_id=grade.id).all()
        print(f"{grade.level} (ID: {grade.id}): {len(streams)} streams")
        for stream in streams:
            print(f"  - Stream {stream.name} (ID: {stream.id})")
