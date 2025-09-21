# P0 Implementation Plan (Non-Invasive)

Goal: Add foundations for flexible assessment weighting, missing-mark handling, and grading without changing current behavior.

Scope (no behavior change):

- Add a standalone `MarkCalculator` service (not wired yet).
- Add minimal data model proposal for grading, weights, and missing marks (documentation only for now).
- Document priorities and acceptance criteria for P0 roll-in.

## Why this order?

- Establishes a single source of truth for marks computation.
- Enables per-school configuration next without rework.
- Keeps current flows intact while preparing for opt-in adoption.

## Components

1. MarkCalculator (standalone):

   - Input: assessments with score/max/status; school config for weights and grading; missing-mark policy.
   - Output: final numeric, grade, points, breakdown, warnings, applied policies.
   - Non-invasive: not called by existing code yet.

2. Config Seeds (later sprints):

   - Assessment weights per school (OPENER/MIDTERM/ENDTERM).
   - Grading scheme bands per school; rounding mode.
   - Missing-mark policies (ABS/EXC/MED/NA/INC) per school.

3. UI/CSV Enhancements (later sprints):
   - Marks entry: numeric or status (mutually exclusive).
   - CSV: support `status` column.

## Acceptance Criteria for P0 Scaffolding

- MarkCalculator exists with typed interface, tests can target it in isolation.
- No changes to controllers/templates; current behavior unaffected.
- Documentation for schema and rollout plan present.

## Roll-in Plan (next)

- Add minimal models/migrations for grading, weights, missing-mark policy.
- Implement a thin adapter in report builders to optionally use MarkCalculator behind a feature flag.
- Update marks upload UI + CSV to support statuses behind a feature flag.
