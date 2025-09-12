"""Generate an up-to-date route inventory for the classteacher blueprint.

Outputs a markdown table similar to ROUTE_INDEX.md with:
- Rule (path)
- Endpoint (function name)
- Methods
- Category guess (CORE/AUX/DEV/LEGACY) using heuristics & template usage

Heuristics:
- If view function decorated with dev_only -> DEV
- If rule contains 'test', 'debug' and not dev_only -> LEGACY
- If referenced in templates (regex match on url_for) -> CORE (unless dev)
- If contains api/, ajax, or methods POST only -> AUX (unless template marking overrides)

Run with: `python -m scripts.generate_route_index`
"""
from __future__ import annotations
import os, re, inspect, sys, json
from collections import defaultdict
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import new_structure  # type: ignore
from new_structure import create_app  # type: ignore

TEMPLATE_DIR = ROOT / 'templates'
ROUTE_INDEX_FILE = ROOT / 'ROUTE_INDEX_AUTO.md'
TARGET_BLUEPRINT = 'classteacher'

# Simple regex to find url_for('classteacher.xxx') occurrences
URL_FOR_PATTERN = re.compile(r"url_for\(\s*['\"]classteacher\.([a-zA-Z0-9_]+)['\"]")


def collect_template_endpoints() -> set[str]:
    refs = set()
    if TEMPLATE_DIR.exists():
        for path in TEMPLATE_DIR.rglob('*.html'):
            try:
                text = path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            for m in URL_FOR_PATTERN.finditer(text):
                refs.add(m.group(1))
    return refs


def guess_category(rule, endpoint_name, func_obj, template_refs):
    name_lower = endpoint_name.lower()
    rule_lower = rule.lower()
    source = inspect.getsource(func_obj)

    # DEV check
    if '@dev_only' in source:
        return 'DEV'

    # Template reference => CORE (unless looks purely data)
    if endpoint_name in template_refs:
        # If clear data route pattern but referenced, still mark CORE
        return 'CORE'

    # Legacy / debug heuristics
    if any(x in rule_lower for x in ['test', 'debug']) or any(x in name_lower for x in ['test', 'debug']):
        return 'LEGACY'

    # Auxiliary/data heuristics
    if any(x in rule_lower for x in ['api/', 'ajax', 'download_', 'upload_', 'add_', 'delete_', 'edit_', 'submit_', 'generate_', 'export', 'bulk', 'get_']):
        return 'AUX'

    # Default fallback
    return 'CORE'


def main():
    app = create_app()
    template_refs = collect_template_endpoints()

    rows = []
    with app.app_context():
        for rule in app.url_map.iter_rules():
            if not rule.endpoint.startswith(f'{TARGET_BLUEPRINT}.'):
                continue
            endpoint_name = rule.endpoint.split('.', 1)[1]
            func = app.view_functions.get(rule.endpoint)
            if func is None:
                continue
            methods = sorted(m for m in rule.methods if m not in {'HEAD', 'OPTIONS'})
            category = guess_category(str(rule), endpoint_name, func, template_refs)
            rows.append({
                'rule': str(rule),
                'endpoint': endpoint_name,
                'methods': ','.join(methods),
                'category': category
            })

    # Sort rows by category then rule
    rows.sort(key=lambda r: (r['category'], r['rule']))

    # Emit markdown
    lines = [
        '# AUTO-GENERATED Classteacher Route Index',
        '',
        'Regenerate via: `python -m scripts.generate_route_index`',
        '',
        'Legend: CORE = template-linked/main, AUX = supporting/data, DEV = dev gated, LEGACY = debug/unused candidates.',
        '',
        f'Template endpoint references detected: {len(template_refs)}',
        '',
        '| Category | Methods | Path | Endpoint |',
        '|----------|---------|------|----------|'
    ]
    for r in rows:
        lines.append(f"| {r['category']} | {r['methods']} | {r['rule']} | {r['endpoint']} |")

    ROUTE_INDEX_FILE.write_text('\n'.join(lines), encoding='utf-8')
    print(f"Wrote {ROUTE_INDEX_FILE} with {len(rows)} routes.")

    # Also emit JSON for tooling
    (ROOT / 'route_index.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
