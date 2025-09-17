import pytest
from new_structure.extensions import db
from new_structure.services.class_report_builder import ClassReportBuilder
from new_structure.models.academic import Grade, Stream, Term, AssessmentType, Subject, Student, Mark

@pytest.fixture(autouse=True)
def _seed_builder_data(app):
    # Rely on baseline seed for Grade 4 / Stream A / Term 1 / Opener / subjects
    with app.app_context():
        grade = Grade.query.filter_by(name='Grade 4').first()
        stream = Stream.query.filter_by(name='A', grade_id=grade.id).first()
        term = Term.query.filter_by(name='Term 1').first()
        assess = AssessmentType.query.filter_by(name='Opener').first()
        subj_math = Subject.query.filter_by(name='Mathematics').first()
        subj_eng = Subject.query.filter_by(name='English').first()
        # Students & marks
        if not Student.query.filter_by(admission_number='A001').first():
            s1 = Student(name='Alice', admission_number='A001', grade_id=grade.id, stream_id=stream.id)
            s2 = Student(name='Bob', admission_number='A002', grade_id=grade.id, stream_id=stream.id)
            db.session.add_all([s1, s2])
            db.session.commit()
        s1 = Student.query.filter_by(admission_number='A001').first()
        s2 = Student.query.filter_by(admission_number='A002').first()
        if not Mark.query.first():
            m1 = Mark(student_id=s1.id, subject_id=subj_math.id, term_id=term.id, assessment_type_id=assess.id, grade_id=grade.id, stream_id=stream.id, raw_mark=80, raw_total_marks=100)
            m2 = Mark(student_id=s2.id, subject_id=subj_math.id, term_id=term.id, assessment_type_id=assess.id, grade_id=grade.id, stream_id=stream.id, raw_mark=60, raw_total_marks=100)
            m3 = Mark(student_id=s1.id, subject_id=subj_eng.id, term_id=term.id, assessment_type_id=assess.id, grade_id=grade.id, stream_id=stream.id, raw_mark=70, raw_total_marks=100)
            db.session.add_all([m1, m2, m3])
            db.session.commit()

@pytest.fixture()
def ctx(app):
    with app.app_context():
        yield

def test_builder_basic(app, ctx):
    result = ClassReportBuilder.build('Grade 4', 'Stream A', 'Term 1', 'Opener')
    assert 'class_data' in result
    assert len(result['class_data']) == 2  # two students
    names = {s['student'] for s in result['class_data']}
    assert names == {'Alice', 'Bob'}
    # Math averages: Alice 80, Bob 60 -> subject average 70
    assert 'Mathematics' in result['subject_averages']
    assert result['subject_averages']['Mathematics'] == 70.0
    # Class average should be computed from filtered totals
    assert result['class_average'] > 0

def test_builder_subject_filter(app, ctx):
    # Only include Mathematics
    from new_structure.models.academic import Subject
    math = Subject.query.filter_by(name='Mathematics').first()
    result = ClassReportBuilder.build('Grade 4', 'Stream A', 'Term 1', 'Opener', selected_subject_ids=[math.id])
    assert set(result['subject_names']) == {'Mathematics'}
    # English should not appear
    for s in result['class_data']:
        assert 'English' not in s.get('filtered_marks', {})

