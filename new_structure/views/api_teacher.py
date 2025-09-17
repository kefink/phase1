"""Minimal teacher API endpoints for authorization tests.

Provides a horizontally sensitive resource `/api/teacher/<int:teacher_id>` that
can only be accessed by:
  * The teacher themselves (session.teacher_id == teacher_id)
  * A headteacher (or elevated admin style roles)

Response intentionally minimal (id, username, role) to avoid PII expansion.
"""
from flask import Blueprint, jsonify, abort, session, request

api_teacher_bp = Blueprint('api_teacher', __name__, url_prefix='/api')

@api_teacher_bp.route('/teacher/<int:teacher_id>', methods=['GET'])
def get_teacher_self_or_head(teacher_id: int):
    """Return teacher basics if requester is self or headteacher.

    Security semantics:
      * 401 if unauthenticated
      * 403 if authenticated but not self nor headteacher
      * 404 if teacher not found (only after authZ check to avoid oracle)  
    """
    if not (session.get('teacher_id') and session.get('role')):
        abort(401, description='Authentication required')
    current_id = session.get('teacher_id')
    role = session.get('role')
    if str(current_id) != str(teacher_id) and role not in ('headteacher', 'admin', 'superadmin'):
        abort(403, description='Forbidden')
    try:
        from ..models.user import Teacher
        teacher = Teacher.query.get(teacher_id)
    except Exception:
        teacher = None
    if not teacher:
        abort(404, description='Not found')
    return jsonify({'id': teacher.id, 'username': teacher.username, 'role': teacher.role})

@api_teacher_bp.route('/class-sample')
def class_sample():
    """Demonstration endpoint using Marshmallow validation.

    Query Params: grade (required), stream (optional)
    Returns normalized payload or 400 on validation error.
    """
    try:
        from ..utils.schemas import GradeStreamQuerySchema
        schema = GradeStreamQuerySchema()
        data = schema.load({'grade': request.args.get('grade'), 'stream': request.args.get('stream')})
    except Exception as e:
        abort(400, description=f'Validation error: {e}')
    return jsonify({'status': 'ok', 'grade': data['grade'], 'stream': data.get('stream')})

__all__ = ['api_teacher_bp']
