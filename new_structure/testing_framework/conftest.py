"""
Global pytest configuration and fixtures for Hillview testing.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    from new_structure import create_app

    app = create_app('testing')
    
    with app.app_context():
        from new_structure.extensions import db
        db.create_all()
        
        # Create test data
        from testing_framework.factories.user_factory import create_test_users
        create_test_users()
        
        yield app
        
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()

@pytest.fixture
def authenticated_headteacher(client):
    """Login as headteacher and return session."""
    response = client.post('/admin_login', data={
        'username': 'test_headteacher',
        'password': 'test123'
    })
    assert response.status_code == 302
    return client

@pytest.fixture
def authenticated_classteacher(client):
    """Login as classteacher and return session."""
    response = client.post('/classteacher_login', data={
        'username': 'test_classteacher',
        'password': 'test123'
    })
    assert response.status_code == 302
    return client

@pytest.fixture
def authenticated_teacher(client):
    """Login as teacher and return session."""
    response = client.post('/teacher_login', data={
        'username': 'test_teacher',
        'password': 'test123'
    })
    assert response.status_code == 302
    return client

@pytest.fixture(scope="session")
def browser():
    """Setup Playwright browser for E2E tests."""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            yield browser
            browser.close()
    except ImportError:
        pytest.skip("Playwright not installed")

@pytest.fixture
def page(browser):
    """Create new page for each test."""
    page = browser.new_page()
    yield page
    page.close()

@pytest.fixture
def base_url():
    """Base URL for testing."""
    return "http://localhost:5000"
