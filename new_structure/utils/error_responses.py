from flask import jsonify

# Standard error format generator
# code: machine readable string
# message: human readable
# details: optional dict with field-level or contextual metadata

def error_response(code: str, message: str, http_status: int = 400, details: dict | None = None):
    payload = {
        'error': {
            'code': code,
            'message': message
        }
    }
    if details:
        payload['error']['details'] = details
    return jsonify(payload), http_status
