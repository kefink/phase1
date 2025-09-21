# Schema Proposal for Flexible Reporting (P0 foundations)

Note: Documentation only; no migrations applied in P0 to avoid behavior changes.

## Tables

1. grading_schemes

- id (PK)
- school_id (FK schools)
- name (string)
- rounding_mode (enum: ROUND_HALF_UP, FLOOR, CEIL, TRUNC)

2. grading_bands

- id (PK)
- scheme_id (FK grading_schemes)
- min_inclusive (float)
- max_inclusive (float)
- grade (string)
- points (float)
- remark (string, optional)

3. assessments

- id (PK)
- school_id (FK schools)
- code (string: OPENER, MIDTERM, ENDTERM, ...)
- display_name (string)
- is_core (bool)

4. subject_weight_policies

- id (PK)
- school_id (FK schools)
- level (string, optional)
- subject_id (FK subjects, optional for defaults)
- assessment_id (FK assessments)
- weight (float)
- drop_lowest_n (int, default 0)
- cap (float, optional)

5. missing_mark_policies

- id (PK)
- school_id (FK schools)
- assessment_id (FK assessments, nullable)
- status_code (enum: ABS, EXC, MED, NA, INC)
- treatment (enum: zero, exclude, proxy)
- requires_comment (bool, default false)

## Notes

- Minimal set supports OPENER/MIDTERM/ENDTERM weighting, grading bands, and missing-mark policies per school.
- Composite subjects and ranking policies can be added later.
