import os
import pytest
from new_structure import create_app

@pytest.fixture()
def app():
    os.environ['TEST_SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app = create_app('testing')
    # Simulate HTTPS enforcement to trigger HSTS
    app.config['FORCE_HTTPS'] = True
    return app

@pytest.fixture()
def client(app):
    return app.test_client()

def test_security_headers_present(client):
    resp = client.get('/')
    # Basic headers
    assert resp.headers.get('X-Frame-Options') == 'DENY'
    assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
    assert resp.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
    assert 'geolocation=()' in resp.headers.get('Permissions-Policy', '')
    # CSP minimal checks
    csp = resp.headers.get('Content-Security-Policy')
    assert csp and "default-src 'self'" in csp
    assert 'script-src' in csp
    # HSTS (since FORCE_HTTPS=True)
    hsts = resp.headers.get('Strict-Transport-Security')
    assert hsts and 'max-age=' in hsts

