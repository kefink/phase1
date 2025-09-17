"""Tests for /api/teacher/<id> horizontal access control.

Covers:
  * 401 unauthenticated
  * 403 different teacher (non-head)
  * 200 self access
  * 200 headteacher accessing another teacher
"""
import pytest
from flask import session

@pytest.mark.usefixtures('app', 'client', 'db_session')
class TestTeacherApiAuthorization:
    def test_unauthenticated_returns_401(self, client):
        resp = client.get('/api/teacher/1')
        assert resp.status_code == 401

    def test_self_access_200(self, client, db_session):
        # Create a teacher user
        from new_structure.models.user import Teacher
        t = Teacher(username='selfuser', password='pw', role='teacher')
        db_session.add(t)
        db_session.commit()
        # Simulate login
        with client.session_transaction() as sess:
            sess['teacher_id'] = t.id
            sess['role'] = 'teacher'
        resp = client.get(f'/api/teacher/{t.id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id'] == t.id
        assert data['username'] == 'selfuser'

    def test_cross_access_forbidden(self, client, db_session):
        from new_structure.models.user import Teacher
        a = Teacher(username='auser', password='pw', role='teacher')
        b = Teacher(username='buser', password='pw', role='teacher')
        db_session.add_all([a, b])
        db_session.commit()
        with client.session_transaction() as sess:
            sess['teacher_id'] = a.id
            sess['role'] = 'teacher'
        resp = client.get(f'/api/teacher/{b.id}')
        assert resp.status_code == 403

    def test_headteacher_access_other(self, client, db_session):
        from new_structure.models.user import Teacher
        # Reuse baseline-seeded headteacher if present to avoid UNIQUE collisions
        head = Teacher.query.filter_by(username='head', role='headteacher').first()
        if not head:
            head = Teacher(username='head', password='pw', role='headteacher')
            db_session.add(head)
            db_session.flush()
        sub = Teacher(username='sub', password='pw', role='teacher')
        db_session.add(sub)
        db_session.commit()
        with client.session_transaction() as sess:
            sess['teacher_id'] = head.id
            sess['role'] = 'headteacher'
        resp = client.get(f'/api/teacher/{sub.id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id'] == sub.id
        assert data['username'] == 'sub'
