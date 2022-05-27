from functools import wraps
from json import load

from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from jsonschema import validate


def check_json_middleware(func):
	with open('schema.json') as f:
		schema = load(f)
		# del schema['properties']['email']

	@wraps(func)
	def decorated_func(*args, **kwargs):
		try:
			validate(instance = request.get_json(), schema=schema)
			return func(*args, **kwargs)
		
		except Exception as e:
			print(e)
			return {"error": "No valid JSON"}, 415

	return decorated_func


def check_admin_role(func):
	@jwt_required()
	def decorated_func(*args, **kwargs):
		jwt_data = get_jwt()['sub']

		if jwt_data['role'] != 'admin':
			return {"msg": "You do not have sufficient permissions for this action"}, 403

		return func(*args, **kwargs)

	return decorated_func
