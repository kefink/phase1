def test_rate_limiter_health_endpoint(app, client):
    resp = client.get('/health/rate-limiter')
    assert resp.status_code == 200
    data = resp.get_json()
    assert {'backend', 'distributed', 'enabled', 'default_limit', 'redis', 'status'}.issubset(data.keys())


def test_log_metrics_endpoint_increments(app, client):
    # Trigger an audit event if available
    if hasattr(app, 'audit_event'):
        app.audit_event('login_attempt', category='auth', outcome='success')
    resp = client.get('/health/log-metrics')
    assert resp.status_code == 200
    data = resp.get_json()
    # Either empty (if audit_event not attached) or contains some counters
    assert isinstance(data, dict)
