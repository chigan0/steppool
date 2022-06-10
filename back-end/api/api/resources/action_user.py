from uuid import uuid4
import pickle

import redis
from rq import Queue
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.orm import Session
from sqlalchemy import or_

from api.models.user import User, UserBallance
from api.models.crypto_address import CryptoAddress, BlockchainNetwork
from api.util.middleware import check_json_middleware
from api.util.utils import generator_random_str, create_order_list, \
check_add_delete_order_redis, check_order_id, send_mail, check_token, check_hcaptcha


class UserSignup(Resource): # Endpoint User registration user
	@check_json_middleware
	def post(self):
		data = request.get_json()
		config = current_app.config
		session = Session(bind = current_app.engine)
		
		dd = session.query(User).filter(or_(
				User.username == data['username'],
				User.email == data['email']
		)).one_or_none() # Checking if a user is registered with this email or username
		session.close()

		if dd is None:
			verification_code = generator_random_str(6)
			redis_conn = redis.Redis(connection_pool = current_app.redis_pool)
			p_mydict = pickle.dumps({"email": data['email'],
				"username": data['username'],
				"password": data['password']
			})
			redis_conn.set(verification_code, p_mydict, config['VERIF_EXPIRE'])

			
			current_app.task_queue.enqueue(send_mail, args=("naz.abylai50@gmail.com", "Test mail",
				config['MAIL_USERNAME'],config['MAIL_SERVER'],
				config['MAIL_PORT'], config['MAIL_PASSWORD'], 
				verification_code
			))

			redis_conn.close()
			return {"verification_code": verification_code}
		
		return {"msg": "This email address or username is already registered"}, 409


class MailConfirm(Resource):
	@check_json_middleware
	def post(self):
		verification_code = request.get_json()['verification_code']
		redis_conn = redis.Redis(connection_pool = current_app.redis_pool)
		data_from_redis = redis_conn.get(verification_code)
		config = current_app.config

		if data_from_redis is None:
			redis_conn.close()
			return {"msg": "Not Valid Code"}, 404

		session = Session(bind = current_app.engine)
		user_data_dict = pickle.loads(data_from_redis)
		user_public_id = str(uuid4())

		user_data = User(public_id = user_public_id, email = user_data_dict['email'], 
						username = user_data_dict['username'])
		user_data.set_password_hash(user_data_dict['password'], config['SECRET_KEY'])
		user_data.save_to_db(session)
		access_token, refresh_token = user_data.create_jwt_token()

		user_balance = UserBallance(public_id = user_data.public_id, wallet_id = generator_random_str(15))
		user_balance.save_to_db(session)
		
		redis_conn.delete(verification_code)
		redis_conn.close(), session.close()
		return {"msg": "", "access_token": access_token, "refresh_token": refresh_token}, 201


class ReplenishBalans(Resource):
	def __init__(self):
		self.config = current_app.config
		self.engine = current_app.engine


	@jwt_required()
	def get(self): # Get order Information by order_id
		user_data = get_jwt()['sub']
		redis_data = check_order_id(request, user_data)

		if redis_data is None:
			return {"msg": "Order not specified or does not exist"}, 404

		return redis_data, 200
		

	@jwt_required()
	def post(self): # Create Order
		replenis_amount = request.get_json()['replenishment_amount']
		coin_name = request.get_json()['coin_name']
		network_name = request.get_json()['network_name']

		session = Session(bind = self.engine)
		coin_data, blockchain_data = check_token(session, coin_name, 
			network_name=network_name, get_network_data=True)

		if coin_data is None:
			return {"msg": "A coin with this name does not exist"}, 404

		# Checking already created orders 
		redis_conn = redis.Redis(connection_pool = current_app.redis_pool)
		order_id = generator_random_str(10)
		jwt_user_data = get_jwt()['sub']

		if check_add_delete_order_redis(jwt_user_data['public_id'], order_id) is None:
			return {"msg": "You have reached the limit of 15 orders"}, 412

		# Crete New Order		
		order_list = create_order_list(coin_name, blockchain_data.network_name, 
			blockchain_data.address, blockchain_data.qr_url, replenis_amount, jwt_user_data)
		

		redis_conn.set(order_id, order_list, self.config['USER_CONFIRM_EXPIRE'])
		redis_conn.lpush('pay_order', order_id)

		redis_conn.close(), session.close()
		return {"msg": "Order successfully created", "order_id": order_id}, 200


	@jwt_required()
	def patch(self): # Confirm pay for order
		user_data = get_jwt()['sub']
		redis_data = check_order_id(request, user_data, True)

		if redis_data is None:
			return {"msg": "You are not the originator of this transaction"}, 403

		redis_conn = redis.Redis(connection_pool = current_app.redis_pool)
		redis_data['user_confirm'] = True
		update_order_list = pickle.dumps(redis_data)
		redis_conn.set(request.args.get('order_id'), update_order_list, self.config['ADM_CONFIRM_EXPIRE'])

		redis_conn.close()
		return {}, 200


	@jwt_required()
	def delete(self): # Delete order by order_id
		order_id = request.args.get('order_id')
		user_data = get_jwt()['sub']
		redis_data = check_order_id(request, user_data, True)

		if redis_data is None:
			return {"msg": "You are not the originator of this transaction"}, 403

		redis_conn = redis.Redis(connection_pool = current_app.redis_pool)
		redis_conn.delete(order_id)
		redis_conn.lrem(redis_data['user_public_id'], 1, order_id)
		redis_conn.lrem('pay_order', 1, order_id)

		redis_conn.close()
		return {}, 204
