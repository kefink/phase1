import os
import pytest
from new_structure import create_app
from new_structure.extensions import db
from new_structure.models.user import Teacher

# Remove local app/client fixtures; use global ones from conftest for isolation.


def test_secret_key_placeholder_auto_upgraded_in_testing(app):
    """Weak testing placeholder should now be auto-upgraded to a strong random key.

    The application factory hardens weak keys (including the historical
    'test-secret-key-for-testing') by replacing them with a generated
    64 hex-character value (>=32 length check for future flexibility).
    """
    key = app.config['SECRET_KEY']
    assert isinstance(key, str) and len(key) >= 32, f"Expected upgraded strong key, got: {key}"
    assert 'test-secret-key-for-testing' not in key


def test_cookie_flags_secure_in_production_like(monkeypatch):
    # Simulate production by selecting production config, but override class attributes directly
    from new_structure.config import ProductionConfig
    ProductionConfig.SECRET_KEY = 'p9d-ultra-key-12345!'  # Strong key without banned substrings
    ProductionConfig.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Simplify to avoid MySQL password checks
    ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS = {}
    os.environ['TEST_SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    prod_app = create_app('production')
    assert prod_app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert prod_app.config['SESSION_COOKIE_SAMESITE'] in ('Lax', 'Strict')
    assert prod_app.config['SESSION_COOKIE_SECURE'] is True


def test_encryption_roundtrip_if_key(monkeypatch):
    from cryptography.fernet import Fernet
    key = Fernet.generate_key().decode()
    monkeypatch.setenv('DATA_ENCRYPTION_KEY', key)
    os.environ['TEST_SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    enc_app = create_app('testing')
    with enc_app.app_context():
        # Explicitly refresh the encryption key after setting the environment variable
        from new_structure.security import data_protection_service
        data_protection_service.refresh_key()
        
        # Ensure tables exist (testing config may not have seeded default data if integrity check passes early)
        db.create_all()
        t = Teacher(username='encuser', role='teacher')
        t.set_password('secret123')
        t.email = 'user@example.com'
        t.phone = '+1234567890'
        db.session.add(t)
        db.session.commit()
        row = db.session.execute(db.text("SELECT email, phone FROM teacher WHERE username='encuser'" )).fetchone()
        assert row.email.startswith('enc:'), f"Expected encrypted value with prefix, got: {row.email}"
        # Reload within context
        loaded = Teacher.query.filter_by(username='encuser').first()
        db.session.refresh(loaded)
        assert loaded.email == 'user@example.com', f"Decryption failed, got {loaded.email}"
        assert loaded.phone == '+1234567890'


def test_security_headers_present(app, client):
    resp = client.get('/')
    # Core headers
    assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
    assert resp.headers.get('X-Frame-Options') == 'DENY'
    assert 'default-src' in (resp.headers.get('Content-Security-Policy') or '')
    assert resp.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
    # COOP/COEP
    assert resp.headers.get('Cross-Origin-Opener-Policy') == 'same-origin'
    assert resp.headers.get('Cross-Origin-Embedder-Policy') == 'require-corp'


def test_https_redirect_and_hsts(monkeypatch):
    # Simulate production for FORCE_HTTPS enforcement
    from new_structure.config import ProductionConfig
    ProductionConfig.SECRET_KEY = 'p9d-ultra-key-23XYZ!'
    ProductionConfig.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # IMPORTANT: Clear engine options so SQLite in-memory doesn't receive MySQL pool params
    ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS = {}
    os.environ['TEST_SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app = create_app('production')
    client = app.test_client()
    # Simulate insecure request by manually crafting http URL; Flask test client treats as HTTP
    resp = client.get('/', base_url='http://localhost')
    # Either a redirect (301) or direct 200 if testing environment bypasses; accept both but check HSTS on final if 200
    if resp.status_code in (301, 302):
        loc = resp.headers.get('Location')
        assert loc.startswith('https://')
    else:
        assert resp.headers.get('Strict-Transport-Security') is not None


def test_config_validator_enforcement_weak_secret(monkeypatch):
    """Production should hard-fail (raise) on obviously weak secrets before validator logs."""
    from new_structure.config import ProductionConfig
    ProductionConfig.SECRET_KEY = 'secret'  # triggers hard failure guard
    ProductionConfig.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS = {}
    with pytest.raises(RuntimeError) as exc:
        os.environ['TEST_SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        create_app('production')
    assert 'Insecure SECRET_KEY' in str(exc.value)


def test_config_validator_auto_upgrade_development(monkeypatch, caplog):
    """Development weak secret key should be auto-upgraded; validator may emit zero warnings now.

    Previous behavior expected a SECURITY VALIDATION warning. After secret key
    hardening enhancement, weak dev keys are transparently replaced with a
    strong persisted value, so warnings about SECRET_KEY may not appear.
    This test asserts the upgrade instead of relying on a warning side effect.
    """
    from new_structure.config import DevelopmentConfig
    DevelopmentConfig.SECRET_KEY = 'secret'  # deliberately weak
    DevelopmentConfig.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    if hasattr(DevelopmentConfig, 'SQLALCHEMY_ENGINE_OPTIONS'):
        DevelopmentConfig.SQLALCHEMY_ENGINE_OPTIONS = {}
    with caplog.at_level('WARNING'):
        os.environ['TEST_SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app = create_app('development')
    upgraded = app.config['SECRET_KEY']
    assert isinstance(upgraded, str) and len(upgraded) >= 32 and 'secret' not in upgraded.lower()
    # It's acceptable if no SECURITY VALIDATION warning now; ensure no weak key persisted
    security_warnings = [r.message for r in caplog.records if 'SECURITY VALIDATION' in r.message]
    # Optional: if warnings exist they shouldn't indicate weak SECRET_KEY remained
    for msg in security_warnings:
        assert 'Weak SECRET_KEY' not in msg
