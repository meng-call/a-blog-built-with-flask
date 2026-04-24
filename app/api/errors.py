from flask import jsonify
from . import api
from ..exceptions import ValidationError


def unauthorized(message):
    """返回401未授权错误"""
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


def forbidden(message):
    """返回403禁止访问错误"""
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response


def bad_request(message):
    """返回400错误请求"""
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


@api.errorhandler(ValidationError)
def validation_error(e):
    """处理验证错误"""
    return bad_request(e.args[0] if e.args else 'Validation error')


@api.errorhandler(400)
def bad_request_handler(e):
    return bad_request(str(e))


@api.errorhandler(401)
def unauthorized_error(e):
    return jsonify({'error': 'unauthorized', 'message': str(e)}), 401


@api.errorhandler(403)
def forbidden_error(e):
    return jsonify({'error': 'forbidden', 'message': str(e)}), 403


@api.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'not found', 'message': str(e)}), 404


@api.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'error': 'method not allowed', 'message': str(e)}), 405


@api.errorhandler(500)
def internal_server_error(e):
    return jsonify({'error': 'internal server error', 'message': str(e)}), 500


@api.errorhandler(429)
def too_many_requests(e):
    return jsonify({'error': 'too many requests', 'message': str(e)}), 429
