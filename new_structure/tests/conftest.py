import pytest
from flask import Flask

TEST_DB_URI = 'sqlite:///:memory:'

@pytest.fixture()
def app():
    """Create a new Flask app + fresh in-memory DB per test to ensure isolation."""
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=TEST_DB_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_ENABLED=False,
    )
    from new_structure.extensions import db
    db.init_app(app)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()

@pytest.fixture()
def db_session(app):
    """Return the active db.session (already bound) for direct usage."""
    from new_structure.extensions import db
    # Use nested transaction pattern if desired; for now simple session usage.
    yield db.session
    # Rollback any leftover transaction state to keep memory DB clean (not strictly needed with drop_all per test)
    try:
        db.session.rollback()
    except Exception:
        pass

# Factories
@pytest.fixture()
def grade_factory(db_session):
    from new_structure.models.academic import Grade
    def _create(name, education_level='Primary'):
        g = Grade(name=name, education_level=education_level)
        db_session.add(g)
        db_session.commit()
        return g
    return _create

@pytest.fixture()
def stream_factory(db_session):
    from new_structure.models.academic import Stream
    def _create(name, grade_id):
        s = Stream(name=name, grade_id=grade_id)
        db_session.add(s)
        db_session.commit()
        return s
    return _create

@pytest.fixture()
def student_factory(db_session):
    from new_structure.models.academic import Student
    counter = {'n': 0}
    def _create(grade_id=None, stream_id=None, name=None, promotion_status='active', eligible=True):
        counter['n'] += 1
        student = Student(
            name=name or f"Student {counter['n']}",
            admission_number=f"ADM{1000+counter['n']}",
            grade_id=grade_id,
            stream_id=stream_id,
            is_eligible_for_promotion=eligible,
            promotion_status=promotion_status,
            academic_year='2024-2025'
        )
        db_session.add(student)
        db_session.commit()
        return student
    return _create

@pytest.fixture()
def teacher_factory(db_session):
    from new_structure.models.user import Teacher
    counter = {'n': 0}
    def _create(username=None, role='teacher'):
        counter['n'] += 1
        t = Teacher(
            username=username or f"teacher{counter['n']}",
            role=role,
            password='pbkdf2:dummy'  # hashed-like placeholder to satisfy NOT NULL
        )
        db_session.add(t)
        db_session.commit()
        return t
    return _create
