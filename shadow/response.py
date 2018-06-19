#encoding: utf-8

from flask import jsonify

STATUS_OK = 200
STATUS_PARAMS_ERROR = 400
STATUS_UNAUTHENTICATE = 403
STATUS_SERVER_ERROR = 500

def json(result=None, code=None, errors=None):
    result = result or {}
    errors = errors or {}
    code = code or (STATUS_PARAMS_ERROR if errors else STATUS_OK)
    return jsonify({'code' : code, 'result' : result, 'errors' : errors})