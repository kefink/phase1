import pytest

@pytest.mark.usefixtures('client')
class TestClassteacherInputValidation:
    def test_preview_class_report_invalid_long_params(self, client, monkeypatch):
        # Login as headteacher to bypass auth restrictions and trigger validation only
        with client.session_transaction() as sess:
            sess['role'] = 'headteacher'
            sess['teacher_id'] = 1
        long_grade = 'G' * 101
        resp = client.get(f'/classteacher/preview_class_report/{long_grade}/Stream A/Term 1/Opener', headers={'Accept': 'application/json'})
        assert resp.status_code == 400
        payload = resp.get_json()
        # New unified error envelope: {'error': {'code': 'INVALID_PATH_PARAMS', 'message': 'Invalid path parameters'}}
        assert payload['error']['code'] == 'INVALID_PATH_PARAMS'
        assert 'Invalid path parameters' in payload['error']['message']

    def test_preview_class_report_valid_params(self, client, monkeypatch):
        with client.session_transaction() as sess:
            sess['role'] = 'headteacher'
            sess['teacher_id'] = 1
        resp = client.get('/classteacher/preview_class_report/Grade 5/Stream A/Term 1/Opener')
        # Authorization may still 403 or redirect (302) if downstream logic redirects;
        # treat 200/302/403 as acceptable for validation stage (focus here is validation not auth outcome)
        assert resp.status_code in (200, 302, 403)
