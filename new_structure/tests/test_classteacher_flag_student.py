import pytest
from new_structure.extensions import db
from new_structure.models.user import Teacher
from new_structure.models import Grade, Stream, TeacherSubjectAssignment, Subject, Student, Term, AssessmentType

@pytest.fixture(autouse=True)
def _ensure_flag_student_data(app):
    # Provide Grade 5 variant separate from baseline Grade 4 for these tests
    with app.app_context():
        grade5 = Grade.query.filter_by(name='Grade 5').first()
        if not grade5:
            grade5 = Grade(name='Grade 5', education_level='upper_primary')
            db.session.add(grade5)
            db.session.flush()
        streamA = Stream.query.filter_by(name='A', grade_id=grade5.id).first()
        if not streamA:
            streamA = Stream(name='A', grade_id=grade5.id)
            db.session.add(streamA)
            db.session.flush()
        term1 = Term.query.filter_by(name='Term 1').first()
        if not term1:
            term1 = Term(name='Term 1', is_current=True)
            db.session.add(term1)
        opener = AssessmentType.query.filter_by(name='Opener').first()
        if not opener:
            opener = AssessmentType(name='Opener', is_active=True)
            db.session.add(opener)
        math = Subject.query.filter_by(name='Mathematics').first()
        if not math:
            math = Subject(name='Mathematics', education_level='upper_primary')
            db.session.add(math)
        db.session.flush()
        ct1 = Teacher.query.filter_by(username='ct1').first()
        ct2 = Teacher.query.filter_by(username='ct2').first()
        head = Teacher.query.filter_by(username='head').first()
        # ct1 should reference streamA for class teacher association
        if ct1 and getattr(ct1, 'stream_id', None) != streamA.id:
            ct1.stream_id = streamA.id
        # Ensure class teacher assignment exists
        existing = TeacherSubjectAssignment.query.filter_by(teacher_id=ct1.id, subject_id=math.id, grade_id=grade5.id, stream_id=streamA.id).first()
        if not existing:
            db.session.add(TeacherSubjectAssignment(teacher_id=ct1.id, subject_id=math.id, grade_id=grade5.id, stream_id=streamA.id, is_class_teacher=True))
        # Student
        if not Student.query.filter_by(admission_number='ADM1').first():
            db.session.add(Student(name='Student One', admission_number='ADM1', grade_id=grade5.id, stream_id=streamA.id, gender='M'))
        db.session.commit()

@pytest.fixture
def client(app):  # reuse session-scoped app's client fixture semantics indirectly
    return app.test_client()


def login(client, username, role):
    with client.session_transaction() as sess:
        t = Teacher.query.filter_by(username=username).first()
        sess['teacher_id'] = t.id
        sess['role'] = role


def _url(g_id, s_id, st_id):
    return f'/classteacher/api/class/{g_id}/{s_id}/students/{st_id}/flag'


def test_flag_student_unassigned_forbidden(client):
    login(client, 'ct2', 'classteacher')
    # fetch ids
    g_id = Grade.query.filter_by(name='Grade 5').first().id
    # IMPORTANT: There are multiple streams named 'A' (Grade 4 baseline & Grade 5 for this test).
    # Filter by grade_id to ensure we target the Grade 5 stream; otherwise we may pick Grade 4 A,
    # triggering a grade/stream mismatch and 404 from the endpoint resource validation.
    s_id = Stream.query.filter_by(name='A', grade_id=g_id).first().id
    st_id = Student.query.filter_by(admission_number='ADM1').first().id
    resp = client.post(_url(g_id, s_id, st_id), json={'note': 'Check performance'})
    assert resp.status_code == 403
    assert 'Forbidden' in resp.get_json()['error']


def test_flag_student_assigned_ok(client):
    login(client, 'ct1', 'classteacher')
    g_id = Grade.query.filter_by(name='Grade 5').first().id
    s_id = Stream.query.filter_by(name='A', grade_id=g_id).first().id
    st_id = Student.query.filter_by(admission_number='ADM1').first().id
    resp = client.post(_url(g_id, s_id, st_id), json={'note': 'Follow up'})
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'ok'


def test_flag_student_headteacher_ok(client):
    login(client, 'head', 'headteacher')
    g_id = Grade.query.filter_by(name='Grade 5').first().id
    s_id = Stream.query.filter_by(name='A', grade_id=g_id).first().id
    st_id = Student.query.filter_by(admission_number='ADM1').first().id
    resp = client.post(_url(g_id, s_id, st_id), json={'note': 'Oversight review'})
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'ok'


def test_flag_student_long_note_rejected(client):
    login(client, 'ct1', 'classteacher')
    g_id = Grade.query.filter_by(name='Grade 5').first().id
    s_id = Stream.query.filter_by(name='A', grade_id=g_id).first().id
    st_id = Student.query.filter_by(admission_number='ADM1').first().id
    long_note = 'X' * 600
    resp = client.post(_url(g_id, s_id, st_id), json={'note': long_note})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error']['code'] == 'INVALID_PAYLOAD'
