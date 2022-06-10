import pickle
import asyncio

import redis
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import and_
from sqlalchemy.orm import Session

from api.models.user import User
from api.models.crypto_address import CryptoAddress
from api.util.utils import get_password_hash, generator_random_str, send_mail, check_hcaptcha
from api.util.middleware import check_json_middleware

class UpdateToken(Resource):
	@jwt_required(refresh = True)
	def post(self):
		jti = get_jwt()["jti"]
		identity = get_jwt_identity()
		config = current_app.config
		session = Session(bind = current_app.engine)

		config['jwt_redis_blocklist'].set(jti, "", config['REFRESH_EXPIRES'])
		user_data = session.query(User).filter((User.public_id == identity['public_id'])).first()
		access_token, refresh_token = user_data.create_jwt_token()
		
		session.close()
		return {"access_token": access_token, "refresh_token": refresh_token}


	@jwt_required(verify_type=False)
	def delete(self):
		token = get_jwt()
		jti = token["jti"]
		ttype = token["type"]
		current_app.config['jwt_redis_blocklist'].set(jti, "", ex=current_app.config['ACCESS_EXPIRES'])

		# Returns "Access token revoked" or "Refresh token revoked"
		return {"msg": f"{ttype.capitalize()} token successfully revoked"}, 200


class Signin(Resource): # Endpoint Authorization
	@check_json_middleware
	def post(self):
		email = request.get_json(force = True)['email']
		password_hash = get_password_hash(request.get_json()['password'], current_app.config)
		session = Session(bind = current_app.engine)

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
	def __init__(self):
		self.config = current_app.config
		self.engine = current_app.engine


	@check_json_middleware
	def post(self):
		email = request.get_json()['email']
		password = request.get_json()['password']
		
		session = Session(bind = self.engine)
		user_data = session.query(User).filter(User.email == email).one_or_none()
		session.close()

		if user_data is None:
			return {"msg": "No user found with this email address"}, 404

		user_id = user_data.id
		redis_conn = redis.Redis(connection_pool = current_app.redis_pool)
		new_password_hash = get_password_hash(password, self.config)
		verification_code = generator_random_str(6)

		p_mydict = pickle.dumps({"email": email,"password": new_password_hash, "id": user_id})
		redis_conn.set(verification_code, p_mydict, self.config['VERIF_EXPIRE'])

		current_app.task_queue.enqueue(send_mail, args=("naz.abylai50@gmail.com", "Test mail",
			self.config['MAIL_USERNAME'],self.config['MAIL_SERVER'],
			self.config['MAIL_PORT'], self.config['MAIL_PASSWORD'], 
			verification_code
		))

		return {"reuslt": verification_code}, 200


	@check_json_middleware
	def patch(self):
		verification_code = request.get_json()['verification_code']
		redis_conn = redis.Redis(connection_pool = current_app.redis_pool)
		data_from_redis = redis_conn.get(verification_code)

		if data_from_redis is None:
			return {"msg": "Invalid confirmation code"}, 404
		
		redis_conn.delete(verification_code)
		user_data_dict = pickle.loads(data_from_redis)
		session = Session(bind = self.engine)

		change_user_data = session.query(User).get(user_data_dict['id'])
		change_user_data.password_hash = user_data_dict['password']
		change_user_data.save_to_db(session)
		access_token, refresh_token = change_user_data.create_jwt_token()

		redis_conn.close(), session.close()
		return {"access_token": access_token, "refresh_token": refresh_token}, 200


class GetCoin(Resource):
	def get(self, coin_name):
		session = Session(bind = current_app.engine)
		coin_data = session.query(CryptoAddress).filter(CryptoAddress.coin == coin_name).one_or_none()

		if coin_data is None:
			return {"msg": "No token with that name found"}, 200

		return {"result": coin_data.serialize()}, 200
