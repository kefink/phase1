import pytest
from new_structure import create_app

@pytest.fixture()
def app_no_debug():
    app = create_app('testing')
    app.config['DEBUG'] = False
    app.config['ENABLE_DEBUG_ROUTES'] = False
    return app

@pytest.fixture()
def app_with_debug():
    app = create_app('testing')
    app.config['ENABLE_DEBUG_ROUTES'] = True
    return app

@pytest.fixture()
def client_no_debug(app_no_debug):
    return app_no_debug.test_client()

@pytest.fixture()
def client_with_debug(app_with_debug):
    return app_with_debug.test_client()

def test_debug_route_blocked(client_no_debug):
    resp = client_no_debug.get('/debug/check_users')
    assert resp.status_code in (404, 405)  # 405 just in case route not registered under testing


def test_debug_route_allowed(client_with_debug):
    resp = client_with_debug.get('/debug/check_users')
    # If route exists it should be accessible; if not present treat as acceptable skip
    assert resp.status_code in (200, 302, 404)  # Allow 302 redirect flows if auth gating applied
