import re, pathlib

REQ = pathlib.Path(__file__).resolve().parent.parent / 'requirements.txt'

ALLOWED_RANGE_PREFIXES = { 'coverage' }  # dev-only allowances

def test_no_unpinned_production_dependencies():
    content = REQ.read_text().splitlines()
    in_dev_section = False
    errors = []
    for raw in content:
        line = raw.strip()
        if not line:
            continue
        if line.startswith('#'):
            if line == '# Development and Testing':
                in_dev_section = True
            continue
        # Skip comments appended after a dep by splitting
        dep_part = line.split('#', 1)[0].strip()
        if not dep_part:
            continue
        # Accept editable or direct references (none present currently)
        if dep_part.startswith(('-e', 'git+', 'http://', 'https://')):
            continue
        # Split name and spec
        if '==' in dep_part:
            name, ver = dep_part.split('==', 1)
            name = name.strip()
            # production check
            if not in_dev_section:
                # ensure no additional comparison ops in version
                if any(sym in ver for sym in ['>', '<', '~', '>=', '<=']) and name.lower() not in ALLOWED_RANGE_PREFIXES:
                    errors.append(f"Prod dependency {name} has complex spec {ver}")
            continue
        # If we reach here, spec lacks exact pin
        name_only = dep_part.split('[',1)[0]
        if not in_dev_section and name_only.lower() not in ALLOWED_RANGE_PREFIXES:
            errors.append(f"Prod dependency {name_only} not pinned exactly: {dep_part}")
    assert not errors, 'Unacceptable production dependency specifications:\n' + '\n'.join(errors)
