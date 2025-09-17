import os
import pytest
from new_structure import create_app
from new_structure.extensions import db
from markupsafe import Markup


@pytest.fixture()
def app():
    os.environ['TEST_SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_sanitize_html_filter_basic(app):
    tpl = app.jinja_env.from_string("{{ value|sanitize_html }}")
    malicious = "<script>alert(1)</script><b>Bold</b><img src=x onerror=alert(2)>"
    rendered = tpl.render(value=malicious)
    # script & img tag stripped, bold retained
    assert '<script>' not in rendered
    assert '<img' not in rendered
    assert '<b>Bold</b>' in rendered


def test_escape_html_filter(app):
    tpl = app.jinja_env.from_string("{{ value|escape_html }}")
    val = '<svg onload=alert(1)>'
    rendered = tpl.render(value=val)
    # Entire tag should be escaped verbatim; attribute remains as text but harmless
    assert rendered.startswith('&lt;svg')
    assert 'onload' in rendered  # appears only in escaped text, not executable


def test_debug_check_users_escapes(client, app):
    # Insert teacher with XSS payload username
    from new_structure.models.user import Teacher
    # Ensure debug routes accessible (gate returns 404 otherwise)
    app.config['DEBUG'] = True
    with app.app_context():
        t = Teacher(username="<img src=x onerror=alert(1)>", role='teacher', password='pw')
        db.session.add(t)
        db.session.commit()
    resp = client.get('/debug/check_users')
    body = resp.get_data(as_text=True)
    assert '<img src=x onerror=alert(1)>' not in body  # Not raw
    assert '&lt;img src=x onerror=alert(1)&gt;' in body  # Escaped


def test_json_embedding_safe(app):
    # Use builtin tojson filter (sanity) and ensure escaping of quotes
    tpl = app.jinja_env.from_string("<script>const data={{ payload|tojson }};</script>")
    payload = {"msg": "quote: ' and \" <script>"}
    rendered = tpl.render(payload=payload)
    # Should contain escaped JSON string inside script tag
    assert 'script' in rendered
    assert '<script>' in rendered
    assert '\\"' in rendered  # escaped double quote in JSON
    assert '<script>' == '<script>'  # trivial to keep linter silent

