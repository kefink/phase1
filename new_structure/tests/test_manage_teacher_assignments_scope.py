import pytest
import os
from flask import Flask, session, Blueprint
from new_structure.extensions import db
from new_structure.views.classteacher import classteacher_bp
from new_structure.models import Teacher, Grade, Subject, Stream, TeacherSubjectAssignment

@pytest.fixture()
def app():
    # Point Flask at the real templates directory so render_template can find assignment template
    templates_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    app = Flask(__name__, template_folder=templates_path)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test'
    db.init_app(app)
    # Provide a csrf_token() callable expected by templates
    @app.context_processor
    def inject_csrf():
        return {'csrf_token': lambda: 'test-csrf-token'}
    # Dummy auth blueprint to satisfy template links
    auth_bp = Blueprint('auth', __name__)
    @auth_bp.route('/logout')
    def logout_route():
        return 'ok'
    app.register_blueprint(auth_bp)
    app.register_blueprint(classteacher_bp)
    with app.app_context():
        db.create_all()
        # Seed teachers with mandatory fields (password, role)
        t1 = Teacher(username='alpha', password='hashed', role='teacher')
        t2 = Teacher(username='beta', password='hashed', role='teacher')
        db.session.add_all([t1, t2])
        db.session.commit()
        # Seed grade/stream/subject
        g = Grade(name='Grade 4', education_level='upper_primary')
        s = Subject(name='Mathematics', education_level='upper_primary')
        db.session.add_all([g, s])
        db.session.commit()
        stream = Stream(name='A', grade_id=g.id)
        db.session.add(stream)
        db.session.commit()
        # Assignment for beta only
        assign = TeacherSubjectAssignment(teacher_id=t2.id, subject_id=s.id, grade_id=g.id, stream_id=stream.id, is_class_teacher=False)
        db.session.add(assign)
        db.session.commit()
    yield app

@pytest.fixture()
def client(app):
    return app.test_client()

# Helper to login teacher id into session
@pytest.fixture()
def login_alpha(app, client):
    with client.session_transaction() as sess:
        alpha = Teacher.query.filter_by(username='alpha').first()
        sess['teacher_id'] = alpha.id
        sess['role'] = 'teacher'  # not privileged global scope
    return client

@pytest.fixture()
def login_alpha_as_class_teacher(app, client):
    with client.session_transaction() as sess:
        alpha = Teacher.query.filter_by(username='alpha').first()
        sess['teacher_id'] = alpha.id
        sess['role'] = 'classteacher'  # privileged (allowed global)
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
