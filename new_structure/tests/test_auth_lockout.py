import os
import pytest
from datetime import datetime, timedelta
from new_structure.models.user import Teacher
from new_structure.extensions import db, csrf, limiter
from flask import Blueprint

@pytest.fixture()
def app():  # independent app fixture for this test module
    from new_structure import create_app
    test_app = create_app('testing')
    # Inject test template path
    test_templates = os.path.join(os.path.dirname(__file__), 'templates')
    if test_templates not in test_app.jinja_loader.searchpath:
        test_app.jinja_loader.searchpath.insert(0, test_templates)

    # Disable limiter during this test module to simplify assertions
    test_app.config['RATELIMIT_ENABLED'] = False

    from new_structure.extensions import db
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def teacher_user(app):
    with app.app_context():
        t = Teacher(username='lockuser', role='teacher')
        t.set_password('goodpass1')
        db.session.add(t)
        db.session.commit()
        return t.id  # Return ID to avoid detached instance issues

def login(client, username, password):
    return client.post('/teacher_login', data={'username': username, 'password': password}, follow_redirects=True)

def test_failed_attempts_increment_and_lockout(app, client, teacher_user):
    # 4 failed attempts (below threshold)
    for _ in range(4):
        resp = login(client, 'lockuser', 'wrongpass')
        assert b'Invalid credentials' in resp.data
    # Re-query to avoid detached instance issues
    teacher_user_db = Teacher.query.get(teacher_user)
    assert teacher_user_db.failed_login_attempts == 4
    assert teacher_user_db.locked_until is None

    # 5th failed attempt triggers lock
    resp = login(client, 'lockuser', 'wrongpass')
    teacher_user_db = Teacher.query.get(teacher_user)
    assert teacher_user_db.failed_login_attempts == 5
    assert teacher_user_db.locked_until is not None

    # Attempt with correct password while locked
    resp = login(client, 'lockuser', 'goodpass1')
    assert b'Invalid credentials' in resp.data  # masked response

    # Manually expire lock
    teacher_user_db.locked_until = datetime.utcnow() - timedelta(minutes=1)
    db.session.commit()

    # Successful login resets counters
    resp = login(client, 'lockuser', 'goodpass1')
    teacher_user_db = Teacher.query.get(teacher_user)
    assert teacher_user_db.failed_login_attempts == 0
    assert teacher_user_db.locked_until is None

def test_session_rotation_on_login(app, client, teacher_user):
    # First login
    resp1 = login(client, 'lockuser', 'goodpass1')
    assert b'Dashboard' in resp1.data or resp1.status_code in (302, 200)
    # Capture session cookie value
    # Retrieve session cookie value
    cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')
    raw_cookie1 = client.get_cookie(cookie_name)
    assert raw_cookie1 is not None
    cookie1_value = raw_cookie1.value if hasattr(raw_cookie1, 'value') else raw_cookie1

    # Logout
    client.get('/logout')

    # Second login triggers rotation (cookie value should differ)
    resp2 = login(client, 'lockuser', 'goodpass1')
    raw_cookie2 = client.get_cookie(cookie_name)
    assert raw_cookie2 is not None
    cookie2_value = raw_cookie2.value if hasattr(raw_cookie2, 'value') else raw_cookie2
    # Value should change due to rotation logic clearing session
    assert cookie1_value != cookie2_value
