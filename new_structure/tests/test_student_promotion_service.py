import pytest
from new_structure.services.student_promotion_service import StudentPromotionService

@pytest.mark.usefixtures('db_session')
class TestStudentPromotionValidation:
    def test_validate_missing_students(self):
        valid, msg = StudentPromotionService.validate_promotion_data({'academic_year_to': '2025-2026', 'students': []})
        assert not valid
        assert 'No students' in msg

    def test_validate_missing_academic_year(self):
        valid, msg = StudentPromotionService.validate_promotion_data({'students': [{'student_id': 1, 'action': 'promote', 'to_grade_id': 2}]})
        assert not valid
        assert 'Target academic year' in msg

    def test_validate_promote_missing_target_grade(self):
        valid, msg = StudentPromotionService.validate_promotion_data({'academic_year_to': '2025-2026', 'students': [{'student_id': 1, 'action': 'promote'}]})
        assert not valid
        assert 'Target grade' in msg

    def test_validate_valid_payload(self):
        payload = {
            'academic_year_to': '2025-2026',
            'students': [
                {'student_id': 1, 'action': 'promote', 'to_grade_id': 2},
                {'student_id': 2, 'action': 'repeat'},
                {'student_id': 3, 'action': 'transfer'},
                {'student_id': 4, 'action': 'graduate'}
            ]
        }
        valid, msg = StudentPromotionService.validate_promotion_data(payload)
        assert valid
        assert msg == ''

@pytest.mark.usefixtures('db_session')
class TestStudentPromotionProcessing:
    def setup_entities(self, grade_factory, stream_factory, student_factory):
        # Create grade progression GRADE 1 -> GRADE 2 -> GRADE 3 -> GRADE 4
        g1 = grade_factory('GRADE 1', 'Primary')
        g2 = grade_factory('GRADE 2', 'Primary')
        g3 = grade_factory('GRADE 3', 'Primary')
        g4 = grade_factory('GRADE 4', 'Primary')
        s1 = stream_factory('A', g1.id)
        s2 = stream_factory('A', g2.id)
        s3 = stream_factory('A', g3.id)
        s4 = stream_factory('A', g4.id)
        st1 = student_factory(grade_id=g1.id, stream_id=s1.id)  # promote
        st2 = student_factory(grade_id=g2.id, stream_id=s2.id)  # repeat
        st3 = student_factory(grade_id=g3.id, stream_id=s3.id)  # transfer
        st4 = student_factory(grade_id=g4.id, stream_id=s4.id)  # graduate scenario (not final but treated differently in test)
        return (g1, g2, g3, g4, st1, st2, st3, st4)

    def test_bulk_promotion_success_mixed(self, grade_factory, stream_factory, student_factory, teacher_factory, db_session):
        g1, g2, g3, g4, st1, st2, st3, st4 = self.setup_entities(grade_factory, stream_factory, student_factory)
        teacher = teacher_factory(role='headteacher')
        # We will treat st4 as graduate even if not final grade to test pathway
        data = {
            'academic_year_to': '2025-2026',
            'students': [
                {'student_id': st1.id, 'action': 'promote', 'to_grade_id': g2.id, 'to_stream_id': None},
                {'student_id': st2.id, 'action': 'repeat'},
                {'student_id': st3.id, 'action': 'transfer'},
                {'student_id': st4.id, 'action': 'graduate'}
            ]
        }
        result = StudentPromotionService.process_bulk_promotion(data, promoted_by_teacher_id=teacher.id)
        # Expect rollback because graduate on non-final grade is allowed by service? It doesn't validate final grade.
        # process_bulk_promotion only validates structure; graduate path does not check final grade.
        assert result['success'] is True
        assert result['processed_count'] == 4
        assert result['promoted_count'] == 1
        assert result['repeated_count'] == 1
        assert result['transferred_count'] == 1
        assert result['graduated_count'] == 1
        assert result['errors'] == []

    def test_bulk_promotion_invalid_target_grade_causes_failure(self, grade_factory, stream_factory, student_factory, teacher_factory, db_session):
        g1 = grade_factory('GRADE 1', 'Primary')
        g2 = grade_factory('GRADE 2', 'Primary')
        s1 = stream_factory('A', g1.id)
        st1 = student_factory(grade_id=g1.id, stream_id=s1.id)
        teacher = teacher_factory()
        # invalid to_grade_id
        data = {
            'academic_year_to': '2025-2026',
            'students': [
                {'student_id': st1.id, 'action': 'promote', 'to_grade_id': 99999}
            ]
        }
        result = StudentPromotionService.process_bulk_promotion(data, promoted_by_teacher_id=teacher.id)
        assert result['success'] is False
        assert result['processed_count'] == 0 or result['processed_count'] == 1  # depends on when rollback occurs
        assert len(result['errors']) >= 1

    def test_individual_promotion_missing_grade(self, grade_factory, stream_factory, student_factory, teacher_factory, db_session):
        g1 = grade_factory('GRADE 1', 'Primary')
        s1 = stream_factory('A', g1.id)
        st1 = student_factory(grade_id=g1.id, stream_id=s1.id)
        teacher = teacher_factory()
        data = {
            'academic_year_to': '2025-2026',
            'students': [
                {'student_id': st1.id, 'action': 'promote'}
            ]
        }
        result = StudentPromotionService.process_bulk_promotion(data, promoted_by_teacher_id=teacher.id)
        assert result['success'] is False
        # Validation stage failure returns 'error' field and empty errors list
        assert 'Target grade required' in result.get('error', '') or 'Target grade' in result.get('error', '')
