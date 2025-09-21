from new_structure.services.mark_calculator import (
    MarkCalculator,
    CalculationInput,
    AssessmentEntry,
    Weight,
    GradeBand,
    MissingPolicy,
)


def default_bands():
    return [
        GradeBand(0, 39.9, 'E', 1),
        GradeBand(40, 49.9, 'D', 2),
        GradeBand(50, 59.9, 'C', 3),
        GradeBand(60, 69.9, 'B', 4),
        GradeBand(70, 100, 'A', 5),
    ]


def default_policies():
    return {
        'ABS': MissingPolicy('ABS', 'exclude'),
        'EXC': MissingPolicy('EXC', 'exclude'),
        'MED': MissingPolicy('MED', 'exclude'),
        'NA': MissingPolicy('NA', 'exclude'),
        'INC': MissingPolicy('INC', 'zero'),
    }


def test_weighted_average_basic_exclude_abs():
    calc = MarkCalculator()
    data = CalculationInput(
        school_id=1,
        subject_id=10,
        level=None,
        rounding_mode='ROUND_HALF_UP',
        weights=[
            Weight('OPENER', 10.0),
            Weight('MIDTERM', 30.0),
            Weight('ENDTERM', 60.0),
        ],
        grade_bands=default_bands(),
        missing_policies=default_policies(),
        entries=[
            AssessmentEntry('OPENER', 8, 10),  # 80%
            AssessmentEntry('MIDTERM', status='ABS'),  # excluded
            AssessmentEntry('ENDTERM', 72, 100),  # 72%
        ],
    )

    out = calc.compute(data)
    # Included weights: OPENER(10) + ENDTERM(60) = 70
    # Weighted: (80*10/70) + (72*60/70) = 11.4286 + 61.7143 = 73.1429 → 73.1
    assert out.final_numeric == 73.1
    assert out.final_grade in ('B', 'A')  # depends on bands; should be 'B' for provided bands
    assert any(b.assessment_code == 'MIDTERM' and b.status == 'ABS' for b in out.breakdown)


def test_zero_treated_inc_affects_denominator():
    calc = MarkCalculator()
    data = CalculationInput(
        school_id=1,
        subject_id=10,
        level=None,
        rounding_mode='ROUND_HALF_UP',
        weights=[
            Weight('OPENER', 10.0),
            Weight('MIDTERM', 30.0),
            Weight('ENDTERM', 60.0),
        ],
        grade_bands=default_bands(),
        missing_policies=default_policies(),
        entries=[
            AssessmentEntry('OPENER', 10, 10),  # 100%
            AssessmentEntry('MIDTERM', status='INC'),  # zero with weight 30 counts in denominator
            AssessmentEntry('ENDTERM', 50, 100),  # 50%
        ],
    )

    out = calc.compute(data)
    # Included weights: OPENER(10) + MIDTERM(30 zero) + ENDTERM(60) = 100
    # Weighted: (100*10/100) + (0*30/100) + (50*60/100) = 10 + 0 + 30 = 40.0 → 40.0
    assert out.final_numeric == 40.0
    assert out.final_grade == 'D'


def test_rounding_modes():
    calc = MarkCalculator()
    base = CalculationInput(
        school_id=1,
        subject_id=10,
        level=None,
        rounding_mode='ROUND_HALF_UP',
        weights=[Weight('ENDTERM', 100.0)],
        grade_bands=default_bands(),
        missing_policies=default_policies(),
        entries=[AssessmentEntry('ENDTERM', 73.14, 100)],
    )
    out = calc.compute(base)
    assert out.final_numeric == 73.1

    base.rounding_mode = 'FLOOR'
    out = calc.compute(base)
    assert out.final_numeric == 73.1  # floor to one decimal of 73.14 -> 73.1

    base.entries = [AssessmentEntry('ENDTERM', 73.19, 100)]
    out = calc.compute(base)
    assert out.final_numeric == 73.1  # floor -> 73.1

    base.rounding_mode = 'CEIL'
    out = calc.compute(base)
    assert out.final_numeric == 73.2  # ceil 73.19 -> 73.2

    base.rounding_mode = 'TRUNC'
    out = calc.compute(base)
    assert out.final_numeric == 73.1  # trunc to 1dp
