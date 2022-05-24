from uuid import uuid4
from random import randint
import pickle

import redis
from flask import request, current_app, jsonify, Response
from flask_restful import Resource
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exc, or_, and_

from api.models.user import User
from api.util.middleware import check_json_middleware


class UserGet(Resource): # Endpoint user get data
	@jwt_required()
	def get(self, user_id):
		if len(user_id) == 36:# Checking the length of the public id
			session = current_app.config['db_connect']
			user_db_data = session.query(User).filter(User.public_id == user_id)

			if user_db_data.count() > 0:
				user_data = user_db_data.first().serialize

				session.close()
				return {'data': user_data}

			session.close()
		return {'results': "User with this user_id not found"}


class UserSignup(Resource): # Endpoint User registration user
	@check_json_middleware
	def post(self):
		data = request.get_json()
		config = current_app.config

		session = config['db_connect']
		dd = session.query(User).filter(or_(
				User.username == data['username'],
				User.email == data['email']
		))# Checking if a user is registered with this email or username

		if dd.count() == 0:
			verification_code = ''.join([str(randint(0,9)) for i in range(6)])
			redis_conn = redis.Redis()
			p_mydict = pickle.dumps({
					"email": data['email'],
					"username": data['username'],
					"password": data['password']
				})
			redis_conn.set(verification_code, p_mydict, config['VERIF_EXPIRE'])
			session.close(), redis_conn.close()
			return jsonify(verification_code = verification_code)

		session.close()			
		return jsonify(error = "This email address or username is already registered")


class MailConfirm(Resource):
	@check_json_middleware
	def post(self):
		verification_code = request.get_json()['verification_code']
		redis_conn = redis.Redis()
		data_from_redis = redis_conn.get(verification_code)

		if data_from_redis is None:
			redis_conn.close()
			return {"error": "Not Valid Code"}, 404

		session = current_app.config['db_connect']
		user_data_dict = pickle.loads(data_from_redis)
		user_public_id = str(uuid4())

		user_data = User(public_id = user_public_id, email = user_data_dict['email'], 
						username = user_data_dict['username'])
		user_data.set_password_hash(user_data_dict['password'], current_app.config['SECRET_KEY'])
		user_data.save_to_db()

		redis_conn.delete(verification_code)
		access_token, refresh_token = user_data.create_jwt_token()

		redis_conn.close()
		return {"error": "", "access_token": access_token, "refresh_token": refresh_token}, 201
