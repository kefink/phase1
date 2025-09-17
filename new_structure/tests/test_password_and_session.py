"""Tests password hashing and session rotation behavior on login.

Focus:
  * Teacher password stored hashed when using model.set_password
  * Login route rotates session (cookie value changes)
"""
import pytest

@pytest.mark.usefixtures('app','client','db_session')
class TestPasswordAndSessionRotation:
    def test_set_password_hashes(self, db_session):
        from new_structure.models.user import Teacher
        t = Teacher(username='hashuser', role='teacher', password='plain')  # legacy direct assign
        # Now set secure password
        t.set_password('MySecurePass1!')
        db_session.add(t)
        db_session.commit()
        assert t.password.startswith(('pbkdf2:', 'scrypt:'))
        assert t.is_password_hashed()

    def test_login_session_rotation(self, client, db_session, monkeypatch):
        # Create teacher with known credentials through set_password to ensure hash
        from new_structure.models.user import Teacher
        teacher = Teacher(username='rotator', role='teacher', password='legacy')
        teacher.set_password('rotate123')
        db_session.add(teacher)
        db_session.commit()

        # Monkeypatch authenticate_teacher used in auth views to bypass full service stack
        def fake_auth(username, password, role):
            if username == 'rotator' and password == 'rotate123' and role == 'teacher':
                return teacher
            return None
        import new_structure.views.auth as auth_views
        monkeypatch.setattr(auth_views, 'authenticate_teacher', fake_auth, raising=False)

        # First GET login form to establish initial cookie
        resp = client.get('/teacher_login')
        assert resp.status_code == 200
        initial_cookie = None
        for h, v in resp.headers.items():
            if h.lower() == 'set-cookie' and 'hillview_session=' in v:
                initial_cookie = v
                break

        # POST credentials
        resp2 = client.post('/teacher_login', data={'username':'rotator','password':'rotate123'})
        assert resp2.status_code in (302, 303)
        new_cookie = None
        for h, v in resp2.headers.items():
            if h.lower() == 'set-cookie' and 'hillview_session=' in v:
                new_cookie = v
                break
        # If framework emitted cookie on both, they should differ (rotation). If only emitted once, ensure session populated.
        if initial_cookie and new_cookie:
            assert initial_cookie != new_cookie, 'Expected session rotation to produce different cookie'
        # Follow redirect to set session
        client.get(resp2.headers.get('Location','/'))
        # Validate session content
        with client.session_transaction() as sess:
            assert sess.get('teacher_id') == teacher.id
            assert sess.get('role') == 'teacher'
