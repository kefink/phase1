import os
import pytest


@pytest.mark.usefixtures("db_session")
def test_flag_enabled_combines_assessments(client, app, db_session):
    # Enable feature flag
    app.config['REPORTS_USE_MARK_CALCULATOR'] = True

    from new_structure.models.academic import Grade, Stream, Term, AssessmentType, Subject, Student, Mark
    # Baseline_seed created Grade 4, Stream A, Term 1
    grade = Grade.query.filter_by(name='Grade 4').first()
    stream = Stream.query.filter_by(name='A', grade_id=grade.id).first()
    term = Term.query.filter_by(name='Term 1').first()

    # Ensure needed assessment types exist with variety of naming
    opener = AssessmentType.query.filter_by(name='Opener').first()
    if not opener:
        opener = AssessmentType(name='Opener', is_active=True)
        db_session.add(opener)
    mid = AssessmentType.query.filter_by(name='Midterm').first()
    if not mid:
        mid = AssessmentType(name='Midterm', is_active=True)
        db_session.add(mid)
    endt = AssessmentType.query.filter_by(name='End Term').first()
    if not endt:
        endt = AssessmentType(name='End Term', is_active=True)
        db_session.add(endt)

    math = Subject.query.filter_by(name='Mathematics').first()
    if not math:
        math = Subject(name='Mathematics', education_level='upper_primary')
        db_session.add(math)
    english = Subject.query.filter_by(name='English').first()
    if not english:
        english = Subject(name='English', education_level='upper_primary')
        db_session.add(english)

    db_session.commit()

    # Create two students
    s1 = Student(name='Alice', admission_number='ADM9001', grade_id=grade.id, stream_id=stream.id)
    s2 = Student(name='Bob', admission_number='ADM9002', grade_id=grade.id, stream_id=stream.id)
    db_session.add_all([s1, s2])
    db_session.commit()

    # Insert marks: S1 has all three, S2 missing MIDTERM
    # Use percentages directly via 'percentage' and set consistent totals
    db_session.add_all([
        Mark(student_id=s1.id, subject_id=math.id, term_id=term.id, assessment_type_id=opener.id, grade_id=grade.id, stream_id=stream.id, percentage=80, raw_mark=80, raw_total_marks=100),
        Mark(student_id=s1.id, subject_id=math.id, term_id=term.id, assessment_type_id=mid.id, grade_id=grade.id, stream_id=stream.id, percentage=60, raw_mark=60, raw_total_marks=100),
        Mark(student_id=s1.id, subject_id=math.id, term_id=term.id, assessment_type_id=endt.id, grade_id=grade.id, stream_id=stream.id, percentage=70, raw_mark=70, raw_total_marks=100),
        # Bob: OPENER only
        Mark(student_id=s2.id, subject_id=math.id, term_id=term.id, assessment_type_id=opener.id, grade_id=grade.id, stream_id=stream.id, percentage=90, raw_mark=90, raw_total_marks=100),
        Mark(student_id=s2.id, subject_id=english.id, term_id=term.id, assessment_type_id=endt.id, grade_id=grade.id, stream_id=stream.id, percentage=50, raw_mark=50, raw_total_marks=100),
    ])
    db_session.commit()

    # Fetch report data for final assessment path (alias 'End Term')
    from new_structure.services.report_service import get_class_report_data
    data = get_class_report_data('Grade 4', 'Stream A', 'Term 1', 'End Term')

    assert not data.get('error'), data.get('error')
    # Expect combined Mathematics for Alice ~ 67.0 using default weights 10/30/60:
    # (80*0.1 + 60*0.3 + 70*0.6) = 8 + 18 + 42 = 68.0 (rounded 68.0)
    alice_row = next((r for r in data['class_data'] if r['student'] == 'Alice'), None)
    assert alice_row, 'Alice missing in class_data'
    assert abs(alice_row['marks'].get('Mathematics', 0) - 68.0) < 0.01

    # Bob missing MIDTERM and ENDTERM for Mathematics; policy excludes NA so only OPENER counts
    # Effective included weights: OPENER 10 only -> result 90.0
    bob_row = next((r for r in data['class_data'] if r['student'] == 'Bob'), None)
    assert bob_row, 'Bob missing in class_data'
    assert abs(bob_row['marks'].get('Mathematics', 0) - 90.0) < 0.01


def test_db_configured_weights_override(client, app, db_session):
    app.config['REPORTS_USE_MARK_CALCULATOR'] = True

    from new_structure.models.academic import Grade, Stream, Term, AssessmentType, Subject, Student, Mark
    from new_structure.models.assessment_config import AssessmentWeightsConfig
    import json

    grade = Grade.query.filter_by(name='Grade 4').first()
    stream = Stream.query.filter_by(name='A', grade_id=grade.id).first()
    term = Term.query.filter_by(name='Term 1').first()
    opener = AssessmentType.query.filter_by(name='Opener').first() or AssessmentType(name='Opener', is_active=True)
    mid = AssessmentType.query.filter_by(name='Midterm').first() or AssessmentType(name='Midterm', is_active=True)
    endt = AssessmentType.query.filter_by(name='End Term').first() or AssessmentType(name='End Term', is_active=True)
    for at in (opener, mid, endt):
        if at.id is None:
            db_session.add(at)
    math = Subject.query.filter_by(name='Mathematics').first() or Subject(name='Mathematics', education_level='upper_primary')
    if math.id is None:
        db_session.add(math)
    db_session.commit()

    s1 = Student(name='Carl', admission_number='ADM9101', grade_id=grade.id, stream_id=stream.id)
    db_session.add(s1)
    db_session.commit()

    # Seed custom weights: OPENER 20, MIDTERM 30, ENDTERM 50
    db_session.add(AssessmentWeightsConfig(education_level='upper_primary', weights_json=json.dumps({
        'OPENER': 20.0, 'MIDTERM': 30.0, 'ENDTERM': 50.0
    })))
    db_session.commit()

    # Insert marks for Carl: 50, 50, 50 -> with new weights still 50
    db_session.add_all([
        Mark(student_id=s1.id, subject_id=math.id, term_id=term.id, assessment_type_id=opener.id, grade_id=grade.id, stream_id=stream.id, percentage=50, raw_mark=50, raw_total_marks=100),
        Mark(student_id=s1.id, subject_id=math.id, term_id=term.id, assessment_type_id=mid.id, grade_id=grade.id, stream_id=stream.id, percentage=50, raw_mark=50, raw_total_marks=100),
        Mark(student_id=s1.id, subject_id=math.id, term_id=term.id, assessment_type_id=endt.id, grade_id=grade.id, stream_id=stream.id, percentage=50, raw_mark=50, raw_total_marks=100),
    ])
    db_session.commit()

    from new_structure.services.report_service import get_class_report_data
    data = get_class_report_data('Grade 4', 'Stream A', 'Term 1', 'End Term')
    assert not data.get('error')
    row = next(r for r in data['class_data'] if r['student'] == 'Carl')
    assert abs(row['marks'].get('Mathematics', 0) - 50.0) < 0.01
