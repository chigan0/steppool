from uuid import uuid4
import pickle

import redis
from flask import request, current_app, jsonify, Response
from flask_restful import Resource
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import exc, or_, and_

from api.models.user import User
from api.models.crypto_address import CryptoAddress
from api.util.middleware import check_json_middleware
from api.util.utils import generator_random_str, create_order_list, check_add_delete_order_redis


class UserGet(Resource): # Endpoint user get data
	@jwt_required()
	def get(self, user_id):
		if len(user_id) == 36:# Checking the length of the public id
			session = Session(bind = current_app.config['engine'].conn)
			user_db_data = session.query(User).filter(User.public_id == user_id)

			if user_db_data.count() > 0:
				user_data = user_db_data.first().serialize

				session.close()
				return {'data': user_data}

			session.close()
		return {'msg': "User with this user_id not found"}


class UserSignup(Resource): # Endpoint User registration user
	@check_json_middleware
	def post(self):
		data = request.get_json()
		config = current_app.config

		session = Session(bind = current_app.config['engine'].conn)
		dd = session.query(User).filter(or_(
				User.username == data['username'],
				User.email == data['email']
		))# Checking if a user is registered with this email or username

		if dd.count() == 0:
			verification_code = generator_random_str(6)
			redis_conn = redis.Redis()
			p_mydict = pickle.dumps({
					"email": data['email'],
					"username": data['username'],
					"password": data['password']
				})
			redis_conn.set(verification_code, p_mydict, config['VERIF_EXPIRE'])
			session.close(), redis_conn.close()
			return {"verification_code": verification_code}

		session.close()			
		return {"msg": "This email address or username is already registered"}


class MailConfirm(Resource):
	@check_json_middleware
	def post(self):
		verification_code = request.get_json()['verification_code']
		redis_conn = redis.Redis()
		data_from_redis = redis_conn.get(verification_code)

		if data_from_redis is None:
			redis_conn.close()
			return {"msg": "Not Valid Code"}, 404

		session = Session(bind = current_app.config['engine'].conn)
		user_data_dict = pickle.loads(data_from_redis)
		user_public_id = str(uuid4())

		user_data = User(public_id = user_public_id, email = user_data_dict['email'], 
						username = user_data_dict['username'])
		user_data.set_password_hash(user_data_dict['password'], current_app.config['SECRET_KEY'])
		user_data.save_to_db(session)

		redis_conn.delete(verification_code)
		access_token, refresh_token = user_data.create_jwt_token()

		redis_conn.close()
		return {"msg": "", "access_token": access_token, "refresh_token": refresh_token}, 201


class ReplenishBalans(Resource):
	@jwt_required()
	def get(self): # Get order Information by order_id
		redis_data = self.check_order_id(request)

		if redis_data is None:
			return {"msg": "Order not specified or does not exist"}, 404

		return {"result": redis_data}, 200
		

	@jwt_required()
	def post(self): # Create Order
		replenis_amount = request.get_json()['replenishment_amount']
		coin_name = request.get_json()['coin_name']
		session = Session(bind = current_app.config['engine'].conn)
		coin_data = session.query(CryptoAddress).filter(CryptoAddress.coin == coin_name).one_or_none()

		if coin_data is None:
			return {"msg": "A coin with this name does not exist"}, 404
		
		# Checking already created orders 
		redis_conn = redis.Redis()
		order_id = generator_random_str(10)
		jwt_user_data = get_jwt()['sub']

		if check_add_delete_order_redis(jwt_user_data['public_id'], order_id) is None:
			return {"msg": ""}, 200

		# Crete New Order		
		order_list = create_order_list(coin_name, coin_data.address, coin_data.qr_url, replenis_amount, jwt_user_data)
		redis_conn.set(order_id, order_list, current_app.config['USER_CONFIRM_EXPIRE'])
		redis_conn.lpush('pay_order', order_id)

		redis_conn.close()
		return {"msg": "Order successfully created", "order_id": order_id}, 200


	@jwt_required()
	def patch(self): # Confirm pay for order
		user_data = get_jwt()['sub']
		redis_data = self.check_order_id(request, user_data, True)

		if redis_data is None:
			return {"msg": "You are not the originator of this transaction"}, 403

		redis_conn = redis.Redis()
		redis_data['user_confirm'] = True
		update_order_list = pickle.dumps(redis_data)
		redis_conn.set(request.args.get('order_id'), update_order_list, current_app.config['ADM_CONFIRM_EXPIRE'])

		redis_conn.close()
		return {}, 200


	@jwt_required()
	def delete(self): # Delete order by order_id
		order_id = request.args.get('order_id')
		user_data = get_jwt()['sub']
		redis_data = self.check_order_id(request, user_data, True)

		if redis_data is None:
			return {"msg": "You are not the originator of this transaction"}, 403

		redis_conn = redis.Redis()
		redis_conn.delete(order_id)
		redis_conn.lrem(redis_data['user_public_id'], 1, order_id)
		redis_conn.lrem('pay_order', 1, order_id)

		redis_conn.close()
		return {}, 204


	def check_order_id(self, request, user_data=None, access_rights_check=False):
		order_id = request.args.get('order_id', "232332", str)
		redis_conn = redis.Redis()
		redis_data = redis_conn.get(order_id)

		if order_id is None or redis_data is None:
			return None

		redis_loads_data = pickle.loads(redis_data)

		if access_rights_check:
			if not redis_loads_data['user_public_id'] == user_data['public_id']:
				return None

		redis_conn.close()
		return redis_loads_data
