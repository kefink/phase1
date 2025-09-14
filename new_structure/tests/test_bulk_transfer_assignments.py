import os
import pytest
from flask import Flask, Blueprint
from new_structure.extensions import db
from new_structure.views.classteacher import classteacher_bp
from new_structure.models import Teacher, Grade, Subject, Stream, TeacherSubjectAssignment


@pytest.fixture()
def app():
    templates_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    app = Flask(__name__, template_folder=templates_path)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'bulk-test'
    db.init_app(app)

    # csrf token stub
    @app.context_processor
    def inject_csrf():
        return {'csrf_token': lambda: 'csrf-test'}

    # Dummy auth blueprint for logout link
    auth_bp = Blueprint('auth', __name__)
    @auth_bp.route('/logout')
    def logout_route():
        return 'ok'
    app.register_blueprint(auth_bp)
    app.register_blueprint(classteacher_bp, url_prefix='/classteacher')

    with app.app_context():
        db.create_all()
        # Seed teachers
        t1 = Teacher(username='t_from', password='hash', role='teacher')
        t2 = Teacher(username='t_to', password='hash', role='teacher')
        actor = Teacher(username='actor', password='hash', role='classteacher')  # performing user
        db.session.add_all([t1, t2, actor])
        db.session.commit()

        # Seed academic structure
        g = Grade(name='Grade 5', education_level='upper_primary')
        db.session.add(g)
        db.session.commit()  # ensure g.id is populated
        subj = Subject(name='Science', education_level='upper_primary')
        db.session.add(subj)
        db.session.commit()
        stream = Stream(name='B', grade_id=g.id)
        db.session.add(stream)
        db.session.commit()

        # Subject assignment owned by from teacher
        sa = TeacherSubjectAssignment(teacher_id=t1.id, subject_id=subj.id, grade_id=g.id, stream_id=stream.id, is_class_teacher=False)
        db.session.add(sa)
        # Class teacher assignment owned by from teacher (subject_id supplied to satisfy NOT NULL)
        ca = TeacherSubjectAssignment(teacher_id=t1.id, subject_id=subj.id, grade_id=g.id, stream_id=stream.id, is_class_teacher=True)
        db.session.add(ca)
        db.session.commit()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def login_actor(app, client):
    with client.session_transaction() as sess:
        actor = Teacher.query.filter_by(username='actor').first()
        sess['teacher_id'] = actor.id
        sess['role'] = 'classteacher'
    return client


def _get_ids():
    t_from = Teacher.query.filter_by(username='t_from').first()
    t_to = Teacher.query.filter_by(username='t_to').first()
    subj_assign = TeacherSubjectAssignment.query.filter_by(teacher_id=t_from.id, is_class_teacher=False).first()
    class_assign = TeacherSubjectAssignment.query.filter_by(teacher_id=t_from.id, is_class_teacher=True).first()
    return t_from, t_to, subj_assign, class_assign


def test_granular_subject_transfer(login_actor):
    with login_actor.application.app_context():
        t_from, t_to, subj_assign, _ = _get_ids()
    resp = login_actor.post('/classteacher/bulk_transfer_assignments', data={
        'from_teacher_id': t_from.id,
        'to_teacher_id': t_to.id,
        'selected_assignment_ids': str(subj_assign.id),  # granular only
        'csrf_token': 'csrf-test'
    }, follow_redirects=True)
    assert resp.status_code == 200
    with login_actor.application.app_context():
        moved = TeacherSubjectAssignment.query.get(subj_assign.id)
        assert moved.teacher_id == t_to.id, 'Subject assignment should move to destination teacher'


def test_legacy_broad_class_transfer(login_actor):
    with login_actor.application.app_context():
        t_from, t_to, _, class_assign = _get_ids()
    resp = login_actor.post('/classteacher/bulk_transfer_assignments', data={
        'from_teacher_id': t_from.id,
        'to_teacher_id': t_to.id,
        'transfer_class_teacher': '1',
        'csrf_token': 'csrf-test'
    }, follow_redirects=True)
    assert resp.status_code == 200
    with login_actor.application.app_context():
        updated = TeacherSubjectAssignment.query.get(class_assign.id)
        assert updated.teacher_id == t_to.id, 'Class teacher assignment should transfer via legacy broad flag'


def test_duplicate_skip_for_granular(login_actor):
    # Create duplicate assignment already owned by destination before attempting transfer
    with login_actor.application.app_context():
        t_from, t_to, subj_assign, _ = _get_ids()
        # If destination already has identical subject assignment, create it
        duplicate = TeacherSubjectAssignment(teacher_id=t_to.id, subject_id=subj_assign.subject_id, grade_id=subj_assign.grade_id, stream_id=subj_assign.stream_id, is_class_teacher=False)
        db.session.add(duplicate)
        db.session.commit()
        from_id = t_from.id
        to_id = t_to.id
        subj_id = subj_assign.id

    resp = login_actor.post('/classteacher/bulk_transfer_assignments', data={
        'from_teacher_id': from_id,
        'to_teacher_id': to_id,
        'selected_assignment_ids': str(subj_id),
        'csrf_token': 'csrf-test'
    }, follow_redirects=True)
    assert resp.status_code == 200
    # Expect skipped duplicates note in flash message
    assert 'skipped 1 duplicates' in resp.data.decode('utf-8')
    with login_actor.application.app_context():
        still_owned = TeacherSubjectAssignment.query.get(subj_id)
        assert still_owned.teacher_id == t_from.id, 'Original assignment should remain with source when duplicate exists at destination'


def test_assignments_api(login_actor):
    with login_actor.application.app_context():
        t_from = Teacher.query.filter_by(username='t_from').first()
    resp = login_actor.get(f'/classteacher/api/teacher_assignments/{t_from.id}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    # Should contain both subject and class teacher assignments (2 total)
    assert len(data) >= 2
    keys = set(data[0].keys())
    assert {'id','grade_id','stream_id','subject_id','is_class_teacher','grade_name','stream_name','subject_name'} <= keys
    # At least one subject assignment should expose a human-readable subject_name
    assert any(item.get('subject_name') for item in data if not item.get('is_class_teacher'))
