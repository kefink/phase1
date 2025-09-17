import pytest
from new_structure.extensions import db
from new_structure.models import Grade, Stream, Term, AssessmentType, Subject, Mark, Student, Teacher, TeacherSubjectAssignment

@pytest.fixture(autouse=True)
def seed_subject_report_data(app):
    """Seed entities needed for subject report tests in an idempotent way."""
    with app.app_context():
        # Grade/Stream
        grade = Grade.query.filter_by(name='Grade 5').first()
        if not grade:
            grade = Grade(name='Grade 5')
            db.session.add(grade); db.session.flush()
        stream = Stream.query.filter_by(name='A', grade_id=grade.id).first()
        if not stream:
            stream = Stream(name='A', grade_id=grade.id)
            db.session.add(stream); db.session.flush()
        # Term and AssessmentType
        term = Term.query.filter_by(name='Term 1').first()
        if not term:
            term = Term(name='Term 1', is_current=True)
            db.session.add(term)
        assess = AssessmentType.query.filter_by(name='Opener').first()
        if not assess:
            assess = AssessmentType(name='Opener', is_active=True)
            db.session.add(assess)
        # Subject
        subj = Subject.query.filter_by(name='Mathematics').first()
        if not subj:
            subj = Subject(name='Mathematics', education_level='upper_primary')
            db.session.add(subj); db.session.flush()
        # Students
        st1 = Student.query.filter_by(admission_number='ADM1').first()
        if not st1:
            st1 = Student(name='Alice', admission_number='ADM1')
            db.session.add(st1); db.session.flush()
        st2 = Student.query.filter_by(admission_number='ADM2').first()
        if not st2:
            st2 = Student(name='Bob', admission_number='ADM2')
            db.session.add(st2); db.session.flush()
        # Marks (ensure two marks exist for the subject/grade/stream/term/assessment)
        if not Mark.query.filter_by(student_id=st1.id, subject_id=subj.id, grade_id=grade.id, stream_id=stream.id, term_id=term.id, assessment_type_id=assess.id).first():
            m1 = Mark(grade_id=grade.id, stream_id=stream.id, subject_id=subj.id, term_id=term.id, assessment_type_id=assess.id, student_id=st1.id, raw_mark=80, raw_total_marks=100, percentage=80)
            db.session.add(m1)
        if not Mark.query.filter_by(student_id=st2.id, subject_id=subj.id, grade_id=grade.id, stream_id=stream.id, term_id=term.id, assessment_type_id=assess.id).first():
            m2 = Mark(grade_id=grade.id, stream_id=stream.id, subject_id=subj.id, term_id=term.id, assessment_type_id=assess.id, student_id=st2.id, raw_mark=70, raw_total_marks=100, percentage=70)
            db.session.add(m2)
        # Teachers
        t_assigned = Teacher.query.filter_by(username='t1').first()
        if not t_assigned:
            t_assigned = Teacher(username='t1', role='teacher', password='hash')
            db.session.add(t_assigned); db.session.flush()
        t_other = Teacher.query.filter_by(username='t2').first()
        if not t_other:
            t_other = Teacher(username='t2', role='teacher', password='hash')
            db.session.add(t_other)
        head = Teacher.query.filter_by(username='head').first()
        if not head:
            head = Teacher(username='head', role='headteacher', password='hash')
            db.session.add(head)
        ct = Teacher.query.filter_by(username='ct').first()
        if not ct:
            ct = Teacher(username='ct', role='classteacher', password='hash')
            db.session.add(ct)
        db.session.flush()
        # Assignment
        if not TeacherSubjectAssignment.query.filter_by(teacher_id=t_assigned.id, subject_id=subj.id, grade_id=grade.id, stream_id=stream.id).first():
            assign = TeacherSubjectAssignment(teacher_id=t_assigned.id, subject_id=subj.id, grade_id=grade.id, stream_id=stream.id)
            db.session.add(assign)
        db.session.commit()

def login(client, username, role):
    # Ensure queries happen within the app context of the client
    app = client.application
    with app.app_context():
        user = Teacher.query.filter_by(username=username).first()
        uid = user.id if user else None
    with client.session_transaction() as sess:
        if uid:
            sess['teacher_id'] = uid
        sess['role'] = role

def _ids_for_grade5_A(app):
    """Return (grade_id, stream_id, subject_id, term_id, assessment_id) for Grade 5 A Mathematics/Term 1/Opener."""
    with app.app_context():
        grade = Grade.query.filter_by(name='Grade 5').first()
        stream = Stream.query.filter_by(name='A', grade_id=grade.id).first()
        subj = Subject.query.filter_by(name='Mathematics').first()
        term = Term.query.filter_by(name='Term 1').first()
        assess = AssessmentType.query.filter_by(name='Opener').first()
        return grade.id, stream.id, subj.id, term.id, assess.id

# --- Tests ---

def test_subject_report_forbidden_for_unassigned_teacher(client):
    login(client, 't2', 'teacher')
    gid, sid, subid, tid, aid = _ids_for_grade5_A(client.application)
    resp = client.get(f'/classteacher/subject_report/{gid}/{sid}/{subid}/{tid}/{aid}', headers={'Accept': 'application/json'})
    assert resp.status_code == 403
    body = resp.get_json()
    assert body['error']['code'] == 'FORBIDDEN'


def test_subject_report_allowed_for_assigned_teacher_json(client):
    login(client, 't1', 'teacher')
    gid, sid, subid, tid, aid = _ids_for_grade5_A(client.application)
    resp = client.get(f'/classteacher/subject_report/{gid}/{sid}/{subid}/{tid}/{aid}', headers={'Accept': 'application/json'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'report' in data
    assert data['report']['subject'] == 'Mathematics'
    assert data['report']['statistics']['total_students'] == 2


def test_subject_report_missing_entity_returns_400(client):
    login(client, 't1', 'teacher')
    # Use a non-existent term id 999
    gid, sid, subid, tid, aid = _ids_for_grade5_A(client.application)
    resp = client.get(f'/classteacher/subject_report/{gid}/{sid}/{subid}/999/{aid}', headers={'Accept': 'application/json'})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body['error']['code'] == 'INVALID_REFERENCE'
    assert 'missing' in body['error'].get('details', {})


def test_subject_report_no_marks_404(client):
    # Create scenario with valid entities but different subject without marks
    login(client, 't1', 'teacher')
    # Subject id 2 does not exist -> will be INVALID_REFERENCE, so instead manipulate by using assessment_type 2 that doesn't exist to trigger invalid; we need a no marks case.
    # To simulate no marks, we reference a different assessment_type after seeding one without marks.
    # Simpler: create new assessment type with no marks inside app context.
    from new_structure.extensions import db as _db
    from new_structure.models import AssessmentType as AT
    with client.application.app_context():
        at2 = AT(name='Mid', is_active=True)
        _db.session.add(at2)
        _db.session.commit()
        new_assess_id = at2.id
    gid, sid, subid, tid, _ = _ids_for_grade5_A(client.application)
    resp = client.get(f'/classteacher/subject_report/{gid}/{sid}/{subid}/{tid}/{new_assess_id}', headers={'Accept': 'application/json'})
    assert resp.status_code == 404
    body = resp.get_json()
    assert body['error']['code'] == 'NO_MARKS'


def test_subject_report_headteacher_override(client):
    login(client, 'head', 'headteacher')
    gid, sid, subid, tid, aid = _ids_for_grade5_A(client.application)
    resp = client.get(f'/classteacher/subject_report/{gid}/{sid}/{subid}/{tid}/{aid}', headers={'Accept': 'application/json'})
    assert resp.status_code == 200
    assert 'report' in resp.get_json()


def test_subject_report_classteacher_access(client):
    login(client, 'ct', 'classteacher')
    # Classteacher not explicitly assigned still allowed by role; should produce 200
    gid, sid, subid, tid, aid = _ids_for_grade5_A(client.application)
    resp = client.get(f'/classteacher/subject_report/{gid}/{sid}/{subid}/{tid}/{aid}', headers={'Accept': 'application/json'})
    assert resp.status_code == 200

