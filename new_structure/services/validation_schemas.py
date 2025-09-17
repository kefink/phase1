from marshmallow import Schema, fields, ValidationError, validates

class ClassReportPathSchema(Schema):
    grade = fields.Str(required=True)
    stream = fields.Str(required=True)
    term = fields.Str(required=True)
    assessment_type = fields.Str(required=True, data_key='assessment_type')

    @validates('grade')
    def validate_grade(self, value):
        if len(value) > 100:
            raise ValidationError('grade too long')

    @validates('stream')
    def validate_stream(self, value):
        if len(value) > 50:
            raise ValidationError('stream too long')

    @validates('term')
    def validate_term(self, value):
        if len(value) > 50:
            raise ValidationError('term too long')

    @validates('assessment_type')
    def validate_assessment_type(self, value):
        if len(value) > 50:
            raise ValidationError('assessment_type too long')

class IDListSchema(Schema):
    ids = fields.List(fields.Integer(strict=True), required=True)
