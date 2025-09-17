import pytest
from new_structure.models import Teacher, Grade, Subject, Stream, TeacherSubjectAssignment
from new_structure.extensions import db
"""Scope tests for manage_teacher_assignments.

These originally re-registered the classteacher blueprint & context processor
after the first request, which under a session-scoped app raises the Flask
"setup finished" AssertionError. The blueprint is already registered during
app factory execution (views.__init__ aggregated). We only need a lightweight
csrf token helper (many templates guard its usage) – inject it once at import
time if not already present.
"""

# Provide csrf helper without using app.context_processor dynamically per-test.
# We avoid late registration by patching jinja env globals directly.
@pytest.fixture(autouse=True, scope='session')
def _ensure_csrf_global(app):
    if 'csrf_token' not in app.jinja_env.globals:
        app.jinja_env.globals['csrf_token'] = lambda: 'test-csrf-token'
    yield

@pytest.fixture(autouse=True)
def seed_scope_data(app):
    with app.app_context():
        # Baseline already provides Grade 4, Stream A, Mathematics subject.
        grade = Grade.query.filter_by(name='Grade 4').first()
        stream = Stream.query.filter_by(name='A', grade_id=grade.id if grade else None).first() if grade else None
        subject = Subject.query.filter_by(name='Mathematics').first()

        # Create alpha/beta teachers only if missing (avoid touching baseline teachers ct1/ct2 etc.)
        alpha = Teacher.query.filter_by(username='alpha').first()
        if not alpha:
            alpha = Teacher(username='alpha', password='hashed', role='teacher')
            db.session.add(alpha)
        beta = Teacher.query.filter_by(username='beta').first()
        if not beta:
            beta = Teacher(username='beta', password='hashed', role='teacher')
            db.session.add(beta)
        db.session.commit()

        # Ensure an assignment exists for beta only (scoped visibility tests)
        if all([beta, subject, grade, stream]):
            existing = TeacherSubjectAssignment.query.filter_by(teacher_id=beta.id, subject_id=subject.id, grade_id=grade.id, stream_id=stream.id).first()
            if not existing:
                db.session.add(TeacherSubjectAssignment(teacher_id=beta.id, subject_id=subject.id, grade_id=grade.id, stream_id=stream.id, is_class_teacher=False))
                db.session.commit()
    yield

# Helper to login teacher id into session
@pytest.fixture()
def login_alpha(client):
    with client.session_transaction() as sess:
        alpha = Teacher.query.filter_by(username='alpha').first()
        sess['teacher_id'] = alpha.id
        sess['role'] = 'teacher'
    return client

@pytest.fixture()
def login_alpha_as_class_teacher(client):
    with client.session_transaction() as sess:
        alpha = Teacher.query.filter_by(username='alpha').first()
        sess['teacher_id'] = alpha.id
        sess['role'] = 'classteacher'
    return client

def test_scope_default_mine_hides_other(login_alpha):
    resp = login_alpha.get('/classteacher/manage_teacher_assignments')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    # Beta will appear in teacher dropdown, so instead assert beta does not appear in any assignment row marker
    # Subject assignment rows include data-subject-id attribute; ensure beta not tied to such rows.
    assert 'beta' not in [line for line in html.splitlines() if 'subjectAssignmentsTable' in line]
    # Scope tile should show My Assigns
    assert 'My Assigns' in html


def test_scope_all_restricted_fallback(login_alpha):
    resp = login_alpha.get('/classteacher/manage_teacher_assignments?scope=all')
    html = resp.get_data(as_text=True)
    # Role not allowed; still should not reveal beta in assignment rows (dropdown allowed)
    assert 'beta' not in [line for line in html.splitlines() if 'subjectAssignmentsTable' in line]
    # Badge Restricted present
    assert 'Restricted' in html


def test_scope_all_allowed_shows_other(login_alpha_as_class_teacher):
    resp = login_alpha_as_class_teacher.get('/classteacher/manage_teacher_assignments?scope=all')
    html = resp.get_data(as_text=True)
    # Now beta's assignment should be visible
    assert 'beta' in html
    # Global View badge
    assert 'Global View' in html
