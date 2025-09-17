def test_audit_counters_increment(app, client):
    if not hasattr(app, 'audit_event'):
        # Skip if audit wrapper not present
        return
    before = client.get('/health/log-metrics').get_json() or {}
    app.audit_event('login_attempt', category='auth', outcome='failure')
    app.audit_event('login_attempt', category='auth', outcome='failure')
    after = client.get('/health/log-metrics').get_json()
    # Find key that matches our event pattern
    matching = [k for k in after.keys() if k.startswith('auth:login_attempt:failure')]
    assert matching, "Expected auth:login_attempt:failure counter to be present"
    # Ensure incremented (if existed before) or newly added
    for k in matching:
        assert after[k] >= before.get(k, 0) + 2
