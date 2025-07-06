"""
Student management services for the Hillview School Management System.
"""
from ..models import Student, Stream, Grade, Mark
from ..extensions import db
from sqlalchemy import text

def get_students_by_stream(stream_id):
    """
    Get all students in a stream.
    
    Args:
        stream_id: The stream ID
        
    Returns:
        List of Student objects
    """
    return Student.query.filter_by(stream_id=stream_id).all()

def get_student_by_id(student_id):
    """
    Get a student by ID.
    
    Args:
        student_id: The student ID
        
    Returns:
        Student object if found, None otherwise
    """
    return Student.query.get(student_id)

def get_student_by_admission_number(admission_number):
    """
    Get a student by admission number.
    
    Args:
        admission_number: The student's admission number
        
    Returns:
        Student object if found, None otherwise
    """
    return Student.query.filter_by(admission_number=admission_number).first()

def add_student(name, admission_number, stream_id, gender):
    """
    Add a new student.

    Args:
        name: The student's name
        admission_number: The student's admission number
        stream_id: The stream ID
        gender: The student's gender

    Returns:
        Dictionary with success status and message or student object
    """
    # Check if admission number already exists
    existing_student = get_student_by_admission_number(admission_number)
    if existing_student:
        return {"success": False, "message": f"Admission number '{admission_number}' is already in use."}

    # Check if student name already exists in the stream
    if stream_id:
        existing_student = Student.query.filter_by(name=name, stream_id=stream_id).first()
        if existing_student:
            return {"success": False, "message": f"Student '{name}' already exists in this stream."}

    # Get grade_id from stream if stream_id is provided
    grade_id = None
    if stream_id:
        stream = Stream.query.get(stream_id)
        if stream:
            grade_id = stream.grade_id

    # Create new student
    student = Student(
        name=name,
        admission_number=admission_number,
        stream_id=stream_id,
        grade_id=grade_id,  # Set grade_id based on stream
        gender=gender.lower() if gender else "unknown"
    )

    db.session.add(student)
    db.session.commit()

    return {"success": True, "student": student}

def update_student(student_id, name=None, admission_number=None, stream_id=None, gender=None):
    """
    Update a student's information.
    
    Args:
        student_id: The student ID
        name: The student's name (optional)
        admission_number: The student's admission number (optional)
        stream_id: The stream ID (optional)
        gender: The student's gender (optional)
        
    Returns:
        Dictionary with success status and message or student object
    """
    student = get_student_by_id(student_id)
    if not student:
        return {"success": False, "message": "Student not found."}
    
    # Update fields if provided
    if name:
        student.name = name
    
    if admission_number and admission_number != student.admission_number:
        existing_student = get_student_by_admission_number(admission_number)
        if existing_student and existing_student.id != student_id:
            return {"success": False, "message": f"Admission number '{admission_number}' is already in use."}
        student.admission_number = admission_number
    
    if stream_id is not None:
        student.stream_id = stream_id
        # Update grade_id based on new stream
        if stream_id:
            stream = Stream.query.get(stream_id)
            if stream:
                student.grade_id = stream.grade_id
        else:
            student.grade_id = None
    
    if gender:
        student.gender = gender.lower()
    
    db.session.commit()
    
    return {"success": True, "student": student}

def delete_student(student_id):
    """
    Delete a student.

    Args:
        student_id: The student ID

    Returns:
        Dictionary with success status and message
    """
    from ..models.academic import ComponentMark
    from sqlalchemy import text

    student = get_student_by_id(student_id)
    if not student:
        return {"success": False, "message": "Student not found."}

    try:
        # TEMPORARY FIX: Disable parent email log queries during deletion
        # This prevents schema errors while parent portal is being developed

        # First delete parent-student relationships using raw SQL to avoid ORM issues
        try:
            # Check if parent_student table exists
            result = db.session.execute(text("SHOW TABLES LIKE 'parent_student'"))
            if result.fetchone():
                # Use raw SQL to avoid triggering parent email log queries
                db.session.execute(
                    text("DELETE FROM parent_student WHERE student_id = :student_id"),
                    {"student_id": student.id}
                )
                print(f"Deleted parent-student relationships for student {student.id}")
        except Exception as parent_error:
            # Parent table might not exist or have schema issues, continue with deletion
            print(f"Warning: Could not delete parent relationships: {parent_error}")

        # Delete any parent email logs using raw SQL to avoid ORM schema issues
        try:
            result = db.session.execute(text("SHOW TABLES LIKE 'parent_email_log'"))
            if result.fetchone():
                # Use raw SQL to avoid column schema issues
                db.session.execute(
                    text("DELETE FROM parent_email_log WHERE student_id = :student_id"),
                    {"student_id": student.id}
                )
                print(f"Deleted parent email logs for student {student.id}")
        except Exception as email_log_error:
            # Email log table might have schema issues, continue with deletion
            print(f"Warning: Could not delete parent email logs: {email_log_error}")

        # Delete component marks that reference the marks
        marks = Mark.query.filter_by(student_id=student.id).all()
        for mark in marks:
            # Delete component marks first
            ComponentMark.query.filter_by(mark_id=mark.id).delete()

        # Then delete the marks
        Mark.query.filter_by(student_id=student.id).delete()

        # Finally delete the student
        db.session.delete(student)
        db.session.commit()

        return {"success": True, "message": f"Student '{student.name}' deleted successfully."}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": f"Error deleting student: {str(e)}"}