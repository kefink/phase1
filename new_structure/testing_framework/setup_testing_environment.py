"""
Comprehensive Testing Environment Setup for Hillview School Management System
This script sets up the complete testing infrastructure with all recommended tools.

TESTING STACK:
- E2E Testing: Playwright + Cypress
- API Testing: pytest + Flask test client
- Database Testing: pytest-mysql + Factory Boy
- Security Testing: Custom framework (already implemented)
- Performance Testing: Locust + pytest-benchmark
"""

import subprocess
import sys
import os
from pathlib import Path

class TestingEnvironmentSetup:
    """Setup comprehensive testing environment for Hillview system."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.testing_requirements = [
            # Core testing framework
            'pytest>=7.4.0',
            'pytest-flask>=1.2.0',
            'pytest-cov>=4.1.0',
            'pytest-html>=3.2.0',
            'pytest-xdist>=3.3.1',  # Parallel testing
            
            # API testing
            'requests>=2.31.0',
            'httpx>=0.24.1',
            'pydantic>=2.0.0',
            
            # Database testing
            'pytest-mysql>=2.3.0',
            'factory-boy>=3.3.0',
            'faker>=19.3.0',
            
            # E2E testing
            'playwright>=1.36.0',
            'selenium>=4.11.0',
            
            # Performance testing
            'locust>=2.16.1',
            'pytest-benchmark>=4.0.0',
            
            # Security testing (additional tools)
            'bandit>=1.7.5',
            'safety>=2.3.5',
            
            # Reporting and utilities
            'allure-pytest>=2.13.2',
            'pytest-mock>=3.11.1',
            'pytest-timeout>=2.1.0'
        ]
    
    def install_requirements(self):
        """Install all testing requirements."""
        print("🔧 Installing testing requirements...")
        
        for requirement in self.testing_requirements:
            try:
                print(f"📦 Installing {requirement}...")
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', requirement
                ], check=True, capture_output=True)
                print(f"✅ {requirement} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {requirement}: {e}")
                return False
        
        return True
    
    def setup_playwright(self):
        """Setup Playwright browsers."""
        print("🎭 Setting up Playwright browsers...")
        
        try:
            # Install Playwright
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', 'playwright'
            ], check=True)
            
            # Install browsers
            subprocess.run([
                sys.executable, '-m', 'playwright', 'install'
            ], check=True)
            
            print("✅ Playwright setup complete")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Playwright setup failed: {e}")
            return False
    
    def create_testing_structure(self):
        """Create comprehensive testing directory structure."""
        print("📁 Creating testing directory structure...")
        
        testing_dirs = [
            'testing_framework',
            'testing_framework/e2e_tests',
            'testing_framework/api_tests',
            'testing_framework/database_tests',
            'testing_framework/performance_tests',
            'testing_framework/security_tests',
            'testing_framework/fixtures',
            'testing_framework/factories',
            'testing_framework/utils',
            'testing_framework/reports',
            'testing_framework/config'
        ]
        
        for dir_path in testing_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py files
            init_file = full_path / '__init__.py'
            if not init_file.exists():
                init_file.write_text('"""Testing module."""\n')
        
        print("✅ Testing directory structure created")
        return True
    
    def create_pytest_config(self):
        """Create pytest configuration."""
        print("⚙️ Creating pytest configuration...")
        
        pytest_ini_content = """[tool:pytest]
testpaths = testing_framework
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=new_structure
    --cov-report=html:testing_framework/reports/coverage
    --cov-report=term-missing
    --html=testing_framework/reports/pytest_report.html
    --self-contained-html
    --maxfail=5
    --timeout=300
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    security: Security tests
    performance: Performance tests
    slow: Slow running tests
    database: Database tests
    api: API tests
    frontend: Frontend tests
    headteacher: Headteacher role tests
    classteacher: Classteacher role tests
    teacher: Teacher role tests
    parent: Parent portal tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
"""
        
        config_file = self.project_root / 'pytest.ini'
        config_file.write_text(pytest_ini_content)
        
        print("✅ pytest configuration created")
        return True
    
    def create_conftest(self):
        """Create main conftest.py with fixtures."""
        print("🔧 Creating conftest.py with fixtures...")
        
        conftest_content = '''"""
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
    
    # Create test configuration
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'FORCE_HTTPS': False,
        'STRICT_ROLE_ENFORCEMENT': False  # Relaxed for testing
    }
    
    app = create_app(test_config)
    
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
'''
        
        conftest_file = self.project_root / 'testing_framework' / 'conftest.py'
        conftest_file.write_text(conftest_content)
        
        print("✅ conftest.py created")
        return True
    
    def create_sample_tests(self):
        """Create sample test files to demonstrate the framework."""
        print("📝 Creating sample test files...")
        
        # API test example
        api_test_content = '''"""
Sample API tests for Hillview School Management System.
"""

import pytest

class TestAuthenticationAPI:
    """Test authentication endpoints."""
    
    def test_admin_login_success(self, client):
        """Test successful admin login."""
        response = client.post('/admin_login', data={
            'username': 'test_headteacher',
            'password': 'test123'
        })
        assert response.status_code == 302
        assert '/headteacher/' in response.location
    
    def test_admin_login_invalid_credentials(self, client):
        """Test admin login with invalid credentials."""
        response = client.post('/admin_login', data={
            'username': 'invalid',
            'password': 'wrong'
        })
        assert response.status_code == 200  # Returns to login page
    
    def test_classteacher_login_success(self, client):
        """Test successful classteacher login."""
        response = client.post('/classteacher_login', data={
            'username': 'test_classteacher',
            'password': 'test123'
        })
        assert response.status_code == 302
        assert '/classteacher/' in response.location

class TestDashboardAPI:
    """Test dashboard endpoints."""
    
    def test_headteacher_dashboard_access(self, authenticated_headteacher):
        """Test headteacher can access dashboard."""
        response = authenticated_headteacher.get('/headteacher/')
        assert response.status_code == 200
    
    def test_classteacher_dashboard_access(self, authenticated_classteacher):
        """Test classteacher can access dashboard."""
        response = authenticated_classteacher.get('/classteacher/')
        assert response.status_code == 200
    
    def test_unauthorized_access_blocked(self, client):
        """Test unauthorized access is blocked."""
        response = client.get('/headteacher/')
        assert response.status_code == 302  # Redirect to login
'''
        
        api_test_file = self.project_root / 'testing_framework' / 'api_tests' / 'test_authentication.py'
        api_test_file.write_text(api_test_content)
        
        # E2E test example
        e2e_test_content = '''"""
Sample E2E tests using Playwright.
"""

import pytest

@pytest.mark.e2e
class TestUserJourneys:
    """Test complete user journeys."""
    
    def test_headteacher_login_journey(self, page, base_url):
        """Test complete headteacher login journey."""
        # Navigate to login page
        page.goto(f"{base_url}/admin_login")
        
        # Fill login form
        page.fill('input[name="username"]', 'test_headteacher')
        page.fill('input[name="password"]', 'test123')
        
        # Submit form
        page.click('button[type="submit"]')
        
        # Verify redirect to dashboard
        page.wait_for_url(f"{base_url}/headteacher/")
        
        # Verify dashboard elements
        assert page.is_visible('text=Dashboard')
        assert page.is_visible('text=Welcome')
    
    def test_classteacher_marks_upload(self, page, base_url):
        """Test classteacher marks upload journey."""
        # Login as classteacher
        page.goto(f"{base_url}/classteacher_login")
        page.fill('input[name="username"]', 'test_classteacher')
        page.fill('input[name="password"]', 'test123')
        page.click('button[type="submit"]')
        
        # Navigate to marks upload
        page.click('text=Upload Marks')
        
        # Verify marks upload page
        assert page.is_visible('text=Upload Marks')
        assert page.is_visible('select[name="grade"]')
'''
        
        e2e_test_file = self.project_root / 'testing_framework' / 'e2e_tests' / 'test_user_journeys.py'
        e2e_test_file.write_text(e2e_test_content)
        
        print("✅ Sample test files created")
        return True
    
    def run_setup(self):
        """Run complete testing environment setup."""
        print("🚀 SETTING UP COMPREHENSIVE TESTING ENVIRONMENT")
        print("=" * 60)
        
        steps = [
            ("Installing testing requirements", self.install_requirements),
            ("Setting up Playwright", self.setup_playwright),
            ("Creating testing structure", self.create_testing_structure),
            ("Creating pytest configuration", self.create_pytest_config),
            ("Creating conftest.py", self.create_conftest),
            ("Creating sample tests", self.create_sample_tests)
        ]
        
        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            if not step_func():
                print(f"❌ Failed: {step_name}")
                return False
        
        print("\n🎉 TESTING ENVIRONMENT SETUP COMPLETE!")
        print("=" * 60)
        print("✅ All testing tools installed")
        print("✅ Testing structure created")
        print("✅ Configuration files ready")
        print("✅ Sample tests available")
        print()
        print("🚀 NEXT STEPS:")
        print("1. Run: pytest testing_framework/api_tests/ -v")
        print("2. Run: pytest testing_framework/e2e_tests/ -v")
        print("3. View coverage: open testing_framework/reports/coverage/index.html")
        print("4. View reports: open testing_framework/reports/pytest_report.html")
        
        return True

if __name__ == '__main__':
    setup = TestingEnvironmentSetup()
    setup.run_setup()
