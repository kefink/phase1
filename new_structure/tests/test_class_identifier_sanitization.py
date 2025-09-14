import pytest

from new_structure.services.class_structure_service import ClassStructureService

@pytest.mark.parametrize(
    "raw,expected_grade,expected_stream",
    [
        ("Grade 1|A", "Grade 1", "A"),
    ("Grade 2|A; DROP TABLE students;--", "Grade 2", "A DROP TABLE students"),
        ("Grade 3|B|EXTRA", "Grade 3", "B|EXTRA"),  # only first split handled
    ("Grade 4 --comment", "Grade 4", None),
        ("Grade 5|A' OR '1'='1", "Grade 5", "A OR 11"),
        ("   Grade   6   |   Main   ", "Grade 6", "Main"),
    ]
)
def test_parse_class_identifier_sanitization(raw, expected_grade, expected_stream):
    grade, stream = ClassStructureService.parse_class_identifier(raw)
    assert grade == expected_grade
    assert stream == expected_stream


def test_parse_non_string():
    grade, stream = ClassStructureService.parse_class_identifier(12345)
    assert grade == '' and stream is None


def test_overlong_identifier():
    raw = 'G' * 500
    grade, stream = ClassStructureService.parse_class_identifier(raw)
    assert len(grade) == 100
    assert stream is None
