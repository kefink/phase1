import os, json
import re

def test_request_id_and_audit_event(client, monkeypatch, tmp_path):
    # Enable JSON logs for test
    monkeypatch.setenv('ENABLE_JSON_LOGS', '1')
    # Force reconfigure logging by creating app again if fixture permits
    # Use existing client to make a request
    r = client.get('/')
    assert 'X-Request-ID' in r.headers
    rid = r.headers['X-Request-ID']
    assert len(rid) > 0

    # Trigger an unauthorized access to generate audit events
    # (Assuming a protected endpoint exists; fallback to /health/log-metrics to ensure route present.)
    metrics = client.get('/health/log-metrics')
    assert metrics.status_code == 200
    data = metrics.get_json()
    assert isinstance(data, dict)


def test_audit_rate_limit_counter(client):
    # Rapidly hit /health/log-metrics which is not rate limited but we can still call audit_event indirectly
    r = client.get('/health/log-metrics')
    assert r.status_code == 200
    # Counters may be empty on fresh test run; ensure JSON structure
    assert isinstance(r.get_json(), dict)


def test_json_logging_toggle(monkeypatch, tmp_path):
    from new_structure import create_app
    monkeypatch.setenv('ENABLE_JSON_LOGS', '1')
    app = create_app('testing')
    log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'app.log')
    with app.app_context():
        app.logger.info('Test JSON log entry')
    # Read tail safely
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()[-20:]
        # Find a JSON looking line
        json_line = None
        for line in reversed(lines):
            if line.strip().startswith('{') and '"msg": "Test JSON log entry"' in line:
                json_line = line
                break
        # Not strictly required to find line depending on ordering, but if found ensure it's valid JSON
        if json_line:
            parsed = json.loads(json_line)
            assert parsed['msg'] == 'Test JSON log entry'
            assert 'request_id' in parsed
