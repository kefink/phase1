# Database Migrations Guide

This project uses Alembic for schema migrations. Runtime schema patching has been removed; all structural changes **must** go through Alembic.

## 1. Environment Setup

Ensure dependencies are installed:

```
pip install -r requirements.txt
```

Set the database URL (example MySQL):

```
set DB_URL=mysql+pymysql://user:strong_password@localhost/hillview
```

(On bash: `export DB_URL=...`)

## 2. Autogenerate a New Migration

1. Make model changes in `new_structure/models/`.
2. Run:

```
alembic revision --autogenerate -m "describe change"
```

3. Review the generated file in `alembic/versions/` – ensure only intended changes are present (no accidental drops/renames).
4. Apply:

```
alembic upgrade head
```

## 3. Applying Migrations

To upgrade to latest:

```
alembic upgrade head
```

To downgrade one step:

```
alembic downgrade -1
```

To view history:

```
alembic history --verbose
```

## 4. Baseline & Existing Revisions

Current baseline revision: `b698339120d3`.
Subsequent revisions add authentication hardening fields and password hash handling. Do **not** modify historical migrations—create new ones.

## 5. Branch Conflicts

If two developers create migrations off the same head, Alembic will produce a branching head scenario. Resolve by creating a merge revision:

```
alembic merge -m "merge branches" <rev1> <rev2>
```

## 6. Workflow Policy

- No direct DDL in application runtime.
- Each PR altering models must include its Alembic revision.
- Review checklist for a migration PR:
  - [ ] New/modified columns have nullability & defaults explicitly set.
  - [ ] Data migration steps are idempotent / guarded.
  - [ ] Downgrade is implemented or intentionally documented as `raise` if irreversible.
  - [ ] No unintended table/column drops.

## 7. Data Migrations

For complex data transforms:

```
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    example = table('example', column('id', sa.Integer), column('status', sa.String(50)))
    conn = op.get_bind()
    conn.execute(example.update().values(status='active').where(example.c.status.is_(None)))
```

Always guard large updates and test on a staging snapshot first.

## 8. Verifying Fresh Setup

To simulate a clean install:

```
drop database hillview; create database hillview;  # MySQL
alembic upgrade head
python -c "from new_structure import create_app; app=create_app();"  # Should NOT emit runtime schema patch logs
```

## 9. Irreversible Changes

If dropping columns with critical data, consider a soft-delete approach or archive table. If truly irreversible, in `downgrade()`:

```
raise RuntimeError("Irreversible migration")
```

## 10. Troubleshooting

- Missing table after upgrade: ensure model import path is correct in `alembic/env.py`.
- Autogenerate missed a change: the model file might not have been imported—confirm it’s included via `new_structure/models/__init__.py`.
- Duplicate column in autogen: manually edit migration to keep the authoritative column definition; likely prior manual DDL drift.

## 11. CI Recommendation

Add a pipeline step:

```
alembic upgrade head
alembic downgrade base
alembic upgrade head
```

This detects irreversible or inconsistent downgrades early.

---

Maintainer Note: Remove any future attempts at runtime schema alteration; enforce via code review.
