import pickle
from random import randint

import redis
from flask import request, current_app, jsonify, Response
from flask_restful import Resource
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import and_
from sqlalchemy.orm import Session

from api.models.user import User
from api.models.crypto_address import CryptoAddress
from api.util.utils import get_password_hash
from api.util.middleware import check_json_middleware

class UpdateToken(Resource):
	@jwt_required(refresh = True)
	def post(self):
		jti = get_jwt()["jti"]
		identity = get_jwt_identity()
		config = current_app.config
		session = Session(bind = current_app.config['engine'].conn)

		config['jwt_redis_blocklist'].set(jti, "", config['REFRESH_EXPIRES'])
		user_data = session.query(User).filter((User.public_id == identity['public_id'])).first()
		access_token, refresh_token = user_data.create_jwt_token()
		
		session.close()
		return {"access_token": access_token, "refresh_token": refresh_token}


class LogOut(Resource):
	@jwt_required()
	def delete(self):
		jti = get_jwt()["jti"]
		config = current_app.config
		config['jwt_redis_blocklist'].set(jti, "", config['ACCESS_EXPIRES'])

		return {}, 204


class Signin(Resource): # Endpoint Authorization
	@check_json_middleware	
	def post(self):
		email = request.get_json(force = True)['email']
		password_hash = get_password_hash(request.get_json()['password'], current_app.config)

		session = Session(bind = current_app.config['engine'].conn)

		user_data = session.query(User).filter(and_(
				User.email == email,
				User.password_hash == password_hash
		)).one_or_none()
		session.close()

		if user_data is None:
			return {"msg": "Invalid email or password"}, 404

		access_token, refresh_token = user_data.create_jwt_token()
		return {"access_token": access_token, "refresh_token": refresh_token}


class RestorePass(Resource):
	def post(self):
		email = request.get_json()['email']
		password = request.get_json()['new_password']
		config = current_app.config
		
		session = Session(bind = current_app.config['engine'].conn)
		user_data = session.query(User).filter(User.email == email).one_or_none()
		session.close()

		if user_data is None:
			return {"msg": "No user found with this email address"}, 404

		user_id = user_data.id
		redis_conn = redis.Redis()
		new_password_hash = get_password_hash(password, config)
		verification_code = ''.join([str(randint(0,9)) for i in range(6)])

		p_mydict = pickle.dumps({"email": email,"password": new_password_hash, "id": user_id})
		redis_conn.set(verification_code, p_mydict, config['VERIF_EXPIRE'])

		return {"reuslt": verification_code}, 200


	def patch(self):
		config = current_app.config
		verification_code = request.get_json()['verification_code']
		redis_conn = redis.Redis()
		data_from_redis = redis_conn.get(verification_code)

		if data_from_redis is None:
			return {"msg": "Invalid confirmation code"}, 404
		
		redis_conn.delete(verification_code)
		user_data_dict = pickle.loads(data_from_redis)
		session = Session(bind = current_app.config['engine'].conn)

		change_user_data = session.query(User).get(user_data_dict['id'])
		change_user_data.password_hash = user_data_dict['password']
		change_user_data.save_to_db(session)

		redis_conn.close(), session.close()
		return {}, 204


class GetCoin(Resource):
	def get(self, coin_name):
		session = Session(bind = current_app.config['engine'].conn)
		coin_data = session.query(CryptoAddress).filter(CryptoAddress.coin == coin_name).one_or_none()

		if coin_data is None:
			return {"msg": "No token with that name found"}, 200

		return {"result": coin_data.serialize()}, 200