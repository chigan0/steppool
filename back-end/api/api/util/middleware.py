from functools import wraps

from flask import request, current_app
from flask_jwt_extended import jwt_required, get_jwt

from api.util.utils import user_data_validation


def check_json_middleware(func):
	@wraps(func)
	def decorated_func(*args, **kwargs):
		config = current_app.config
		try:
			if user_data_validation(config, request) is not None:
				return func(*args, **kwargs)

		except Exception as e:
			print(e)

		return {"error": "No valid JSON"}, 400

	return decorated_func


def check_admin_role(func):
	@jwt_required()
	def decorated_func(*args, **kwargs):
		jwt_data = get_jwt()['sub']

		if jwt_data['role'] != 'admin':
			return {"msg": "You do not have sufficient permissions for this action"}, 403

		return func(*args, **kwargs)

	return decorated_func
