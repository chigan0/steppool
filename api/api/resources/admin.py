import pickle
import math

import redis
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from api.models.user import User
from api.models.crypto_address import CryptoAddress
from api.util.middleware import check_admin_role


class CoinAddress(Resource):
	def get(self):
		session = Session(bind = current_app.config['engine'].conn)
		coin_data = session.query(CryptoAddress).all()
		coin_list = {}
		
		for i in coin_data:
			coin, address, qr_url = i.elem()
			coin_list["coin_name"] = coin
			coin_list['address'] = address
		#	coin_list['img_url'] = qr_url

		session.close()
		return coin_list, 200

	@check_admin_role
	def post(self):
		coin_name = request.get_json()['coin']
		address = request.get_json()['address']
		qr_url = request.get_json()['qr_url']
		session = Session(bind = current_app.config['engine'].conn)

		coin_data = session.query(CryptoAddress).filter(or_(
			CryptoAddress.coin == coin_name,
			CryptoAddress.address == address))
		
		if coin_data.count() != 0:
			return {"msg": "A coin with this name does not exist."}

		new_coin = CryptoAddress(coin = coin_name, address = address, qr_url = qr_url)
		new_coin.save_to_db(session)
		session.close()

		return {"msg": "Successful"}, 200


	def patch(self):
		pass


	@check_admin_role
	def delete(self):
		return {}, 204


class ConfirmTransaction(Resource):
	@check_admin_role
	def get(self):
		offset = request.args.get("offset", 1, int)
		limit = request.args.get("limit", 15, int)
		per_offset = limit * offset - limit

		redis_conn = redis.Redis()
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


	def post(self):
		pass


	def patch(self):
		pass