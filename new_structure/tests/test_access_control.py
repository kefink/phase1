"""Authorization Layer Tests (A5 Broken Access Control)

Focus:
 1. Authentication required (401)
 2. Role allow-list enforcement (403)
 3. Resource/action permission matrix (headteacher vs teacher)
 4. Class scope enforcement for classteacher with / without permission

Uses lightweight test routes registered dynamically to avoid depending on large view modules.
"""
from flask import Blueprint, jsonify, session
import pytest
from new_structure.security.authorization import enforce, enforce_ownership
from new_structure.models.function_permission import FunctionPermission, DefaultFunctionPermissions
from new_structure.models.permission import ClassTeacherPermission
from new_structure.extensions import db
from new_structure.models.access_audit import AccessAudit
from new_structure.models.user import Teacher
from new_structure.models.academic import Grade, Stream, Subject
from uuid import uuid4


pytestmark = pytest.mark.freshapp

@pytest.fixture()
def auth_bp(fresh_app):
    """Register ephemeral routes for authorization tests."""
    bp = Blueprint('testauth', __name__)

    # Simple resource permission (system_config.read) gated via require_roles through enforce roles param
    @bp.route('/system/ping')
    @enforce('system', 'read', roles=['headteacher'])
    def system_ping():  # noqa: D401
        return jsonify(ok=True)

    # Marks write with class scope
    @bp.route('/marks/<int:grade_id>/<int:stream_id>/update')
    @enforce('marks', 'write', class_scope=True, grade_arg='grade_id', stream_arg='stream_id')
    def update_marks(grade_id, stream_id):  # noqa: D401
        return jsonify(updated=True, grade_id=grade_id, stream_id=stream_id)

    # Function-level: default allowed function (e.g., dashboard)
    @bp.route('/function/default')
    @enforce('marks', 'read', function='dashboard')
    def func_default():  # noqa: D401
        return jsonify(ok=True, function='dashboard')

    # Function-level: restricted function (e.g., manage_students)
    @bp.route('/function/restricted')
    @enforce('marks', 'read', function='manage_students')
    def func_restricted():  # noqa: D401
        return jsonify(ok=True, function='manage_students')

    # Ownership: teacher can only view own profile summary
    @bp.route('/profile/<int:teacher_id>/summary')
    @enforce_ownership(owner_arg='teacher_id', resource='marks', action='read')
    def profile_summary(teacher_id):  # noqa: D401
        return jsonify(ok=True, owner=teacher_id)

    # Subject-level: require subject scope (uses subject name)
    @bp.route('/subject/<subject_name>/view')
    @enforce('marks', 'read')  # base permission; subject enforcement via explicit call inside
    def subject_view(subject_name):  # noqa: D401
        from new_structure.security.authorization import authorize
        authorize('marks', 'read', subject=subject_name)
        return jsonify(ok=True, subject=subject_name)

    fresh_app.register_blueprint(bp)
    yield bp


def login(session_client, teacher_id, role):
    with session_client.session_transaction() as sess:
        sess['teacher_id'] = teacher_id
        sess['role'] = role


@pytest.fixture()
def client(fresh_app):
    return fresh_app.test_client()


def test_authentication_required(fresh_app, client, auth_bp):
    """Unauthenticated request must yield 401."""
    resp = client.get('/marks/1/1/update')
    assert resp.status_code == 401


def test_role_allow_list_enforced(fresh_app, client, auth_bp):
    with fresh_app.app_context():
        head = Teacher(username=f"head_{uuid4().hex[:8]}", role='headteacher', password='x')
        t = Teacher(username=f"t_{uuid4().hex[:8]}", role='teacher', password='x')
        g = Grade(name='Grade 4')
        db.session.add_all([head, t, g]); db.session.flush()
        s = Stream(name='A', grade_id=g.id)
        db.session.add(s); db.session.commit()
        head_id = head.id
        t_id = t.id
    # Teacher lacks required headteacher role for system endpoint
    login(client, t_id, 'teacher')
    resp = client.get('/system/ping')
    assert resp.status_code == 403
    # Headteacher succeeds
    login(client, head_id, 'headteacher')
    resp2 = client.get('/system/ping')
    assert resp2.status_code == 200


def test_class_scope_denied_without_permission(fresh_app, client, auth_bp):
    with fresh_app.app_context():
        ct = Teacher(username=f"ct_{uuid4().hex[:8]}", role='classteacher', password='x')
        g = Grade(name='Grade 5')
        db.session.add_all([ct, g]); db.session.flush()
        s = Stream(name='B', grade_id=g.id)
        db.session.add(s); db.session.commit()
        ct_id, g_id, s_id = ct.id, g.id, s.id
    login(client, ct_id, 'classteacher')
    # No permission record yet -> 403
    resp = client.get(f'/marks/{g_id}/{s_id}/update')
    assert resp.status_code == 403


def test_class_scope_allowed_with_permission(fresh_app, client, auth_bp):
    with fresh_app.app_context():
        ct = Teacher(username=f"ct_{uuid4().hex[:8]}", role='classteacher', password='x')
        g = Grade(name='Grade 6')
        db.session.add_all([ct, g]); db.session.flush()
        s = Stream(name='C', grade_id=g.id)
        db.session.add(s); db.session.commit()
        # Seed permission
        perm = ClassTeacherPermission.grant_permission(
            teacher_id=ct.id,
            grade_id=g.id,
            stream_id=s.id,
            granted_by_id=ct.id  # self-grant in test context acceptable
        )
        ct_id, g_id, s_id = ct.id, g.id, s.id
    assert perm is not None
    login(client, ct_id, 'classteacher')
    resp = client.get(f'/marks/{g_id}/{s_id}/update')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['grade_id'] == g_id and data['stream_id'] == s_id


def test_headteacher_bypasses_class_scope(fresh_app, client, auth_bp):
    with fresh_app.app_context():
        head = Teacher(username=f"head_{uuid4().hex[:8]}", role='headteacher', password='x')
        g = Grade(name='Grade 7')
        db.session.add_all([head, g]); db.session.flush()
        s = Stream(name='D', grade_id=g.id)
        db.session.add(s); db.session.commit()
        head_id, g_id, s_id = head.id, g.id, s.id
    login(client, head_id, 'headteacher')
    resp = client.get(f'/marks/{g_id}/{s_id}/update')
    assert resp.status_code == 200


def test_teacher_requires_permission_same_as_classteacher(fresh_app, client, auth_bp):
    with fresh_app.app_context():
        teacher = Teacher(username=f"t_{uuid4().hex[:8]}", role='teacher', password='x')
        head = Teacher(username=f"head_{uuid4().hex[:8]}", role='headteacher', password='x')
        g = Grade(name='Grade 8')
        db.session.add_all([teacher, head, g]); db.session.flush()
        s = Stream(name='E', grade_id=g.id)
        db.session.add(s); db.session.commit()
        teacher_id, head_id, g_id, s_id = teacher.id, head.id, g.id, s.id
    login(client, teacher_id, 'teacher')
    denied = client.get(f'/marks/{g_id}/{s_id}/update')
    assert denied.status_code == 403
    # Grant permission and retry
    # Direct insert to avoid any name-based lookup paths
    with fresh_app.app_context():
        perm = ClassTeacherPermission(
            teacher_id=teacher_id,
            grade_id=g_id,
            stream_id=s_id,
            granted_by=head_id,
            is_active=True
        )
        db.session.add(perm)
        db.session.commit()
    with fresh_app.app_context():
        assert ClassTeacherPermission.has_permission(teacher_id, g_id, s_id), "Permission record not recognized after direct insert"
    allowed = client.get(f'/marks/{g_id}/{s_id}/update')
    assert allowed.status_code == 200


def test_function_default_allowed_for_classteacher(fresh_app, client, auth_bp):
    with fresh_app.app_context():
        ct = Teacher(username=f"ct_{uuid4().hex[:8]}", role='classteacher', password='x')
        db.session.add(ct); db.session.commit()
        ct_id = ct.id
    login(client, ct_id, 'classteacher')
    resp = client.get('/function/default')
    assert resp.status_code == 200, 'Default allowed function should succeed without explicit permission'


def test_function_restricted_requires_explicit_permission(fresh_app, client, auth_bp):
    with fresh_app.app_context():
        head = Teacher(username=f"head_{uuid4().hex[:8]}", role='headteacher', password='x')
        ct = Teacher(username=f"ct_{uuid4().hex[:8]}", role='classteacher', password='x')
        db.session.add_all([head, ct]); db.session.commit()
        head_id, ct_id = head.id, ct.id
    # Denied first
    login(client, ct_id, 'classteacher')
    denied = client.get('/function/restricted')
    assert denied.status_code == 403
    # Grant explicit permission
    category = DefaultFunctionPermissions.get_function_category('manage_students')
    with fresh_app.app_context():
        perm = FunctionPermission.grant_function_permission(
            teacher_id=ct_id,
            function_name='manage_students',
            function_category=category,
            granted_by_id=head_id,
            scope_type='global'
        )
    assert perm is not None, 'Granting restricted function permission failed'
    # Re-login and retry
    login(client, ct_id, 'classteacher')
    allowed = client.get('/function/restricted')
    assert allowed.status_code == 200, 'Restricted function should succeed after explicit permission grant'


def test_ownership_enforcement_owner_access(fresh_app, client, auth_bp):
    with fresh_app.app_context():
        owner = Teacher(username=f"t_{uuid4().hex[:8]}", role='teacher', password='x')
        db.session.add(owner); db.session.commit()
        owner_id = owner.id
    login(client, owner_id, 'teacher')
    resp = client.get(f'/profile/{owner.id}/summary')
    assert resp.status_code == 200
    assert resp.get_json()['owner'] == owner_id


def test_ownership_enforcement_forbidden_for_other(fresh_app, client, auth_bp):
    with fresh_app.app_context():
        t1 = Teacher(username=f"t_{uuid4().hex[:8]}", role='teacher', password='x')
        t2 = Teacher(username=f"t_{uuid4().hex[:8]}", role='teacher', password='x')
        db.session.add_all([t1, t2]); db.session.commit()
        t1_id, t2_id = t1.id, t2.id
    login(client, t1_id, 'teacher')
    resp = client.get(f'/profile/{t2_id}/summary')
    assert resp.status_code == 403


def test_ownership_enforcement_headteacher_bypass(fresh_app, client, auth_bp):
    with fresh_app.app_context():
        head = Teacher(username=f"head_{uuid4().hex[:8]}", role='headteacher', password='x')
        t = Teacher(username=f"t_{uuid4().hex[:8]}", role='teacher', password='x')
        db.session.add_all([head, t]); db.session.commit()
        head_id, t_id = head.id, t.id
    login(client, head_id, 'headteacher')
    resp = client.get(f'/profile/{t_id}/summary')
    assert resp.status_code == 200


def test_audit_log_records_success_and_denial(fresh_app, client, auth_bp):
    """Verify that both denied and successful attempts create audit rows."""
    # Baseline count
    with fresh_app.app_context():
        start_count = AccessAudit.query.count()
        t = Teacher(username=f"t_{uuid4().hex[:8]}", role='teacher', password='x')
        g = Grade(name='Grade 10')
        db.session.add_all([t, g]); db.session.flush()
        s = Stream(name='A', grade_id=g.id)
        db.session.add(s); db.session.commit()
        t_id, g_id, s_id = t.id, g.id, s.id
    # Attempt class scoped route without permission (deny)
    login(client, t_id, 'teacher')
    denied = client.get(f'/marks/{g_id}/{s_id}/update')
    assert denied.status_code == 403
    with fresh_app.app_context():
        mid_count = AccessAudit.query.count()
    assert mid_count == start_count + 1, 'Denied attempt should create one audit row'
    # Grant permission and retry (success)
    with fresh_app.app_context():
        perm = ClassTeacherPermission.grant_permission(
            teacher_id=t_id, grade_id=g_id, stream_id=s_id, granted_by_id=t_id
        )
    assert perm is not None
    allowed = client.get(f'/marks/{g_id}/{s_id}/update')
    assert allowed.status_code == 200
    with fresh_app.app_context():
        end_count = AccessAudit.query.count()
    assert end_count == mid_count + 1, 'Successful attempt should create additional audit row'
    # Optional: sanity check fields of latest row
    with fresh_app.app_context():
        latest = AccessAudit.query.order_by(AccessAudit.id.desc()).first()
        assert latest.success is True and latest.resource.startswith('marks')


def test_subject_scope_denied_without_assignment(fresh_app, client, auth_bp):
    with fresh_app.app_context():
        head = Teacher(username=f"head_{uuid4().hex[:8]}", role='headteacher', password='x')
        t = Teacher(username=f"t_{uuid4().hex[:8]}", role='teacher', password='x')
        db.session.add_all([head, t]); db.session.commit()
        head_id, t_id = head.id, t.id
    # Teacher not linked to subject 'Mathematics'
    login(client, t_id, 'teacher')
    denied = client.get('/subject/Mathematics/view')
    assert denied.status_code == 403
    # Headteacher bypass
    login(client, head_id, 'headteacher')
    bypass = client.get('/subject/Mathematics/view')
    assert bypass.status_code == 200


def test_subject_scope_allowed_with_assignment(fresh_app, client, auth_bp):
    with fresh_app.app_context():
        t = Teacher(username=f"t_{uuid4().hex[:8]}", role='teacher', password='x')
        db.session.add(t); db.session.commit()
        t_id = t.id
    # Create or fetch subject 'Science'
    with fresh_app.app_context():
        subj = Subject.query.filter_by(name='Science').first()
        if not subj:
            subj = Subject(name='Science', education_level='primary')
            db.session.add(subj)
            db.session.commit()
        # Link teacher to subject via association table
        t2 = Teacher.query.get(t_id)
        t2.subjects.append(subj)
        db.session.commit()
    login(client, t_id, 'teacher')
    allowed = client.get('/subject/Science/view')
    assert allowed.status_code == 200
