import os
import pytest


def test_production_weak_secret_key_enforced(monkeypatch):
    """Creating a production app with weak SECRET_KEY should raise RuntimeError."""
    from new_structure import create_app
    # Ensure environment reflects production
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', 'changeme')
    # Use a safe ephemeral DB to avoid MySQL requirement
    monkeypatch.setenv('DB_URL', 'sqlite:///:memory:')
    with pytest.raises(RuntimeError):
        create_app('production')


def test_non_production_auto_secret_key(monkeypatch):
    """In development a weak key should auto-upgrade to a strong generated key."""
    from new_structure import create_app
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.setenv('SECRET_KEY', 'secret')
    app = create_app('development')
    # Weak value should be replaced with >= 32 hex chars
    assert len(app.config['SECRET_KEY']) >= 32
    assert 'secret' not in app.config['SECRET_KEY'].lower()
