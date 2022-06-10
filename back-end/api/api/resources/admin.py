import pickle
import math

import redis
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from api.models.user import User, UserBallance
from api.models.crypto_address import CryptoAddress, BlockchainNetwork
from api.util.middleware import check_admin_role
from api.util.utils import generator_random_str, check_order_id, check_token


class CoinAddress(Resource):
	def __init__(self):
		self.config = current_app.config
		self.engine = current_app.engine
		if request.method != "GET":
			self.coin_name = request.get_json()['coin']
		else:
			self.coin_name = request.args.get("coin", None, str)


	def get(self):
		session = Session(bind = self.engine)
		
		if self.coin_name is not None:
			coin_data = check_token(session, self.coin_name)
			if coin_data is None:
				return {"msg": "This token is Note"}, 200
			
			network_list = session.query(BlockchainNetwork).filter(BlockchainNetwork.coin_id == coin_data.id).all()
			network_list_result = {}

			for i in network_list:
				network_data = i.serialize_json()
				network_list_result[i.id] = network_data

			session.close()
			return network_list_result, 200
		
		coin_data = session.query(CryptoAddress).all()
		coin_list = {}

		for i in coin_data:
			coin_id, coin_name = i.elem()
			coin_list[coin_id] = coin_name

		session.close()
		return coin_list, 200


	@check_admin_role
	def post(self):
		session = Session(bind = self.engine)
		coin_data = check_token(session, self.coin_name)
		
		if coin_data is not None:
			return {"msg": "A coin with this name does not exist."}

		new_coin = CryptoAddress(coin = self.coin_name)#, address = address, qr_url = qr_url)
		new_coin.save_to_db(session)
		session.close()

		return {"msg": "Successful"}, 200


	@check_admin_role
	def put(self):
		address = request.get_json()['address']
		qr_url = request.get_json()['qr_url']
		network_name = request.get_json()['network_name']
		session = Session(bind = self.engine)
		coin_data = check_token(session, self.coin_name, qr_url=qr_url, address=address, check_network=True)

		if coin_data is None:
			return {"msg": "network with the same name or address or qr url exists"}, 400


		network_ = BlockchainNetwork(coin_id = coin_data.id, network_name = network_name, 
			address = address, qr_url = qr_url)
		network_.save_to_db(session)
		
		session.close()
		return {}, 200


	@check_admin_role
	def delete(self):
		return {}, 204


class ConfirmTransaction(Resource):
	def __init__(self):
		self.config = current_app.config


	@check_admin_role
	def get(self):
		offset = request.args.get("offset", 1, int)
		limit = request.args.get("limit", 15, int)
		per_offset = limit * offset - limit

		redis_conn = redis.Redis(connection_pool = current_app.redis_pool)
		order_list = redis_conn.lrange("pay_order", per_offset, limit * offset - 1)
		resul_dict = {}

		for i in order_list:
			redis_data = redis_conn.get(i)
			if redis_data is None:
				redis_conn.lrem('pay_order', 1, i)
				continue

			redis_loads_data = pickle.loads(redis_data)
			del redis_loads_data['qr_url']
			resul_dict[i.decode('utf-8')] = redis_loads_data

		amount_str = math.ceil(len(redis_conn.lrange("pay_order", 0, -1)) / limit)
		redis_conn.close()

		return {"result": resul_dict, "offset": offset, "amount_str": amount_str}, 200


	@check_admin_role
	def post(self):
		order_data = check_order_id(request)

		if order_data is None or order_data['user_confirm'] is False:
			return {"msg": "The user did not confirm the transaction"}, 412
	
		session = Session(bind = current_app.engine)

		user_balance = session.query(UserBallance).filter(UserBallance.public_id == order_data['user_public_id']).one_or_none()
		user_balance.ballance += float(order_data['amount'])-2
		user_balance.save_to_db(session)

		redis_conn = redis.Redis(connection_pool = current_app.redis_pool)
		redis_conn.delete(request.get_json()['order_id'])
		redis_conn.lrem('pay_order', 1, request.get_json()['order_id'])

		redis_conn.close(), session.close()
		return {}, 200


	def patch(self):
		pass