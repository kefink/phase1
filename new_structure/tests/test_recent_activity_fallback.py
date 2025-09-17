from datetime import datetime, timedelta

def test_recent_activity_fallback_triggers(app, db_session, grade_factory, stream_factory, student_factory, teacher_factory):
    """If there are only old marks (>7 days), fallback path should label entries with '(all-time fallback)'."""
    from new_structure.models.academic import Subject, Term, AssessmentType, Mark, Grade
    from new_structure.services.headteacher_universal_service import HeadteacherUniversalService as H

    # Arrange minimal academic structure
    grade = grade_factory('Grade 1')
    stream = stream_factory('A', grade.id)
    student = student_factory(grade_id=grade.id, stream_id=stream.id)
    subject = Subject(name='Mathematics', education_level='primary')
    # Reuse existing Term 1 from baseline if present to avoid UNIQUE conflicts
    term = Term.query.filter_by(name='Term 1').first()
    if not term:
        term = Term(name='Term 1')
    assess = AssessmentType(name='End Term')
    db_session.add_all([subject, term, assess])
    db_session.commit()

    # Create an old mark (30 days ago)
    old_mark = Mark(
        student_id=student.id,
        subject_id=subject.id,
        term_id=term.id,
        assessment_type_id=assess.id,
        grade_id=grade.id,
        stream_id=stream.id,
        raw_mark=50,
        raw_total_marks=100
    )
    db_session.add(old_mark)
    db_session.commit()
    # Manually backdate created_at
    old_mark.created_at = datetime.utcnow() - timedelta(days=30)
    db_session.commit()

    activity = H._get_recent_activity()
    assert activity, "Expected fallback activity entries"
    assert any('(all-time fallback)' in a['description'] for a in activity), "Fallback label missing"
