import pytest
from new_structure.extensions import db
from new_structure.models.user import Teacher
from new_structure.models import Grade, Stream, TeacherSubjectAssignment, Subject, Term, AssessmentType

@pytest.fixture(autouse=True)
def _ensure_security_data(app):
    with app.app_context():
        g = Grade.query.filter_by(name='Grade 5').first()
        if not g:
            g = Grade(name='Grade 5', education_level='upper_primary')
            db.session.add(g)
            db.session.flush()
        s = Stream.query.filter_by(name='A', grade_id=g.id).first()
        if not s:
            s = Stream(name='A', grade_id=g.id)
            db.session.add(s)
            db.session.flush()
        term = Term.query.filter_by(name='Term 1').first()
        if not term:
            term = Term(name='Term 1', is_current=True)
            db.session.add(term)
        assess = AssessmentType.query.filter_by(name='Opener').first()
        if not assess:
            assess = AssessmentType(name='Opener', is_active=True)
            db.session.add(assess)
        subj = Subject.query.filter_by(name='Mathematics').first()
        if not subj:
            subj = Subject(name='Mathematics', education_level='upper_primary')
            db.session.add(subj)
        db.session.flush()
        ct = Teacher.query.filter_by(username='ct1').first()
        if ct and getattr(ct, 'stream_id', None) != s.id:
            ct.stream_id = s.id
        other = Teacher.query.filter_by(username='ct2').first()
        head = Teacher.query.filter_by(username='head').first()
        if ct and subj and g and s:
            existing = TeacherSubjectAssignment.query.filter_by(teacher_id=ct.id, subject_id=subj.id, grade_id=g.id, stream_id=s.id).first()
            if not existing:
                db.session.add(TeacherSubjectAssignment(teacher_id=ct.id, subject_id=subj.id, grade_id=g.id, stream_id=s.id, is_class_teacher=True))
        db.session.commit()

@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username, role):
    with client.session_transaction() as sess:
        t = Teacher.query.filter_by(username=username).first()
        sess['teacher_id'] = t.id
        sess['role'] = role


def test_preview_class_report_denied_for_unassigned_class(client):
    """Classteacher not assigned to Grade 5 A should be denied (ct2)."""
    login(client, 'ct2', 'classteacher')
    resp = client.get('/classteacher/preview_class_report/Grade 5/Stream A/Term 1/Opener')
    assert resp.status_code == 403


def test_preview_class_report_allowed_for_assigned_class(client):
    login(client, 'ct1', 'classteacher')
    resp = client.get('/classteacher/preview_class_report/Grade 5/Stream A/Term 1/Opener')
    assert resp.status_code == 200


def test_preview_class_report_headteacher_override(client):
    login(client, 'head', 'headteacher')
    resp = client.get('/classteacher/preview_class_report/Grade 5/Stream A/Term 1/Opener')
    assert resp.status_code == 200
