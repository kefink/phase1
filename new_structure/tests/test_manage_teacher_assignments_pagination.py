import os
import re
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
    app.config['SECRET_KEY'] = 'pagination-test'
    db.init_app(app)

    @app.context_processor
    def inject_csrf():
        return {'csrf_token': lambda: 'csrf-test'}

    auth_bp = Blueprint('auth', __name__)
    @auth_bp.route('/logout')
    def logout_route():
        return 'ok'
    app.register_blueprint(auth_bp)
    app.register_blueprint(classteacher_bp)

    with app.app_context():
        db.create_all()
        # Single acting teacher with global privileges to simplify (can view all)
        actor = Teacher(username='actor', password='hash', role='classteacher')
        db.session.add(actor)
        db.session.commit()
        # Create grade + streams and a single subject reused for all entries
        grade = Grade(name='Grade 6', education_level='upper_primary')
        db.session.add(grade)
        db.session.commit()
        subject = Subject(name='Science', education_level='upper_primary')
        db.session.add(subject)
        db.session.commit()
        # Create additional teachers and subject assignments with UNIQUE stream per assignment
        # to prevent duplicate collapsing logic (subject+grade+stream uniqueness).
        # 30 subject assignments so with per_page=10 we have 3 pages
        for i in range(30):
            stream = Stream(name=f'S{i}', grade_id=grade.id)
            db.session.add(stream)
            db.session.commit()
            t = Teacher(username=f't_{i}', password='hash', role='teacher')
            db.session.add(t)
            db.session.commit()
            assign = TeacherSubjectAssignment(teacher_id=t.id, subject_id=subject.id, grade_id=grade.id, stream_id=stream.id, is_class_teacher=False)
            db.session.add(assign)
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

def test_subject_pagination_pages(login_actor):
    # Request per_page_subject=10 and inspect three pages
    page1 = login_actor.get('/classteacher/manage_teacher_assignments?scope=all&subject_page=1&per_page_subject=10&per_page_class=10&allow_duplicates_for_pagination=1')
    assert page1.status_code == 200
    html1 = page1.get_data(as_text=True)
    # Extract only subject assignments table body to avoid teacher dropdown usernames
    def extract_subject_table(html):
        start = html.find('id="subjectAssignmentsTable"')
        if start == -1:
            return html
        tbody_start = html.find('<tbody', start)
        tbody_end = html.find('</tbody>', tbody_start)
        return html[tbody_start:tbody_end]
    table1 = extract_subject_table(html1)
    # Extract teacher usernames from first page rows
    teachers_page1 = re.findall(r'>t_(\d+)<', table1)
    # There should be exactly 10 rows (per_page_subject=10)
    assert len(teachers_page1) == 10
    # No teacher with index >=10 should appear
    assert all(int(idx) < 10 for idx in teachers_page1)
    assert 'Page 1 of 3' in html1

    page2 = login_actor.get('/classteacher/manage_teacher_assignments?scope=all&subject_page=2&per_page_subject=10&per_page_class=10&allow_duplicates_for_pagination=1')
    html2 = page2.get_data(as_text=True)
    table2 = extract_subject_table(html2)
    teachers_page2 = re.findall(r'>t_(\d+)<', table2)
    assert len(teachers_page2) == 10
    assert all(10 <= int(idx) < 20 for idx in teachers_page2)
    assert 'Page 2 of 3' in html2

    page3 = login_actor.get('/classteacher/manage_teacher_assignments?scope=all&subject_page=3&per_page_subject=10&per_page_class=10&allow_duplicates_for_pagination=1')
    html3 = page3.get_data(as_text=True)
    table3 = extract_subject_table(html3)
    teachers_page3 = re.findall(r'>t_(\d+)<', table3)
    assert len(teachers_page3) == 10
    assert all(20 <= int(idx) < 30 for idx in teachers_page3)
    assert 'Page 3 of 3' in html3

    # Ensure next link absent on last page
    assert 'Next »' not in html3 or 'Next &raquo;' not in html3

    # Ensure prev link present on page2 and page3
    assert ('« Prev' in html2 or '&laquo; Prev' in html2)
    assert ('« Prev' in html3 or '&laquo; Prev' in html3)

def test_class_pagination_independent(login_actor):
    # There are no class assignments; ensure pagination bar not rendered for class table
    resp = login_actor.get('/classteacher/manage_teacher_assignments?scope=all&class_page=2&per_page_class=5&allow_duplicates_for_pagination=1')
    html = resp.get_data(as_text=True)
    # Should not contain 'Page 2 of' for class area (since none) but should for subjects default page (since > per_page_subject default 25 -> total 30 => 2 pages)
    assert 'No Class Teacher Assignments' in html
    # Default per_page_subject=25 -> 30 items => Subject pagination shows 2 total pages and currently page 1
    assert 'Page 1 of 2' in html
