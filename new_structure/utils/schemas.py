"""Central Marshmallow schemas (initial scaffold).

Provides a minimal `GradeStreamQuerySchema` used to validate query params
for endpoints needing grade / stream identifiers. This demonstrates schema-
based validation (OWASP A03 injection prevention via structured parsing).
"""
try:
    from marshmallow import Schema, fields, validates_schema, ValidationError
except Exception:  # marshmallow might not yet be installed in current env
    Schema = object  # type: ignore
    fields = type('fields', (), {'Int': int, 'Str': str})  # minimal placeholders
    def validates_schema(*a, **k):
        def wrap(fn):
            return fn
        return wrap
    class ValidationError(Exception):
        pass

class GradeStreamQuerySchema(Schema):
    grade = fields.Str(required=True)
    stream = fields.Str(required=False, allow_none=True)

    @validates_schema
    def validate_lengths(self, data, **kwargs):  # pragma: no cover (simple)
        if len(data['grade']) > 20:
            raise ValidationError('grade too long')
        if data.get('stream') and len(data['stream']) > 20:
            raise ValidationError('stream too long')

__all__ = ['GradeStreamQuerySchema']
