import os
import pytest
from new_structure import create_app
from new_structure.extensions import db
from new_structure.models.user import Teacher

@pytest.fixture()
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()


def test_secret_key_placeholder_not_used_in_testing(app):
    # Testing config intentionally allows placeholder; ensure it's set
    assert app.config['SECRET_KEY'] == 'test-secret-key-for-testing'


def test_cookie_flags_secure_in_production_like(monkeypatch):
    # Simulate production by selecting production config, but override class attributes directly
    from new_structure.config import ProductionConfig
    ProductionConfig.SECRET_KEY = 'p9d-ultra-key-12345!'  # Strong key without banned substrings
    ProductionConfig.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Simplify to avoid MySQL password checks
    ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS = {}
    prod_app = create_app('production')
    assert prod_app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert prod_app.config['SESSION_COOKIE_SAMESITE'] in ('Lax', 'Strict')
    assert prod_app.config['SESSION_COOKIE_SECURE'] is True


def test_encryption_roundtrip_if_key(monkeypatch):
    from cryptography.fernet import Fernet
    key = Fernet.generate_key().decode()
    monkeypatch.setenv('DATA_ENCRYPTION_KEY', key)
    enc_app = create_app('testing')
    with enc_app.app_context():
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
