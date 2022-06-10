from smtplib import SMTP_SSL,SMTP
from ssl import create_default_context,SSLCertVerificationError
from hashlib import pbkdf2_hmac
from random import randint
import asyncio
import re
import pickle

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
from time import time
from sqlalchemy import and_, or_
from aiohttp import ClientSession
import json
import redis
import requests

from api.models.user import User, UserBallance
from api.models.crypto_address import CryptoAddress, BlockchainNetwork


def get_password_hash(password, config):
	return pbkdf2_hmac('sha256', password.encode('utf-8'), config['SECRET_KEY'].encode('utf-8'),100000).hex()


def generator_random_str(str_length):
	return ''.join([str(randint(0,9)) for i in range(str_length)])


def send_mail(email_to, 
		title, mail_username, 
		mail_server, mail_port, 
		mail_password, message = "", 
		path_template = False, kwargs = None):	
	
	s = time()
	
	context = create_default_context()
	msg = MIMEMultipart('alternative')
	msg['Subject'] = title
	msg['From'] = mail_username
	msg['To'] = email_to
	msg['Subject'] = "Dawdawd"

	if path_template:
		html = open(f"templates/{path_template}").read()
		template = Template(html)
		part2 = MIMEText(template.render(kwargs=kwargs), 'html')

	else:
		part2 = MIMEText(message)

	msg.attach(part2)
	try:
		with SMTP_SSL(mail_server, mail_port, context=context) as server:
			server.login(mail_username, mail_password)
			server.send_message(msg)
			server.quit()

	except SSLCertVerificationError as ssl:
		print(ssl)
		
		smtpObj = SMTP(mail_server)
		smtpObj.login(mail_username, mail_password)
		smtpObj.send_message(msg)
		smtpObj.quit()

	except Exception as e:
		print(e)

	finally:
		print(time()-s)
		return


def create_order_list(coin_name, network_name, address, qr_url, amount, jwt_data):
	order_list = pickle.dumps({
		"coin": coin_name,
		"network_name": network_name,
		"address": address,
		"qr_url": qr_url,
		"amount": amount,
		"user_public_id": jwt_data['public_id'],
		"email": jwt_data['email'],
		"user_confirm": False,
		"admin_condirm": False
	})

	return order_list


def check_add_delete_order_redis(user_public_id, order_id):
	redis_conn = redis.Redis()
	order_list = redis_conn.lrange(user_public_id, 0, -1)

	if len(order_list) >= 25:
		return None

	redis_conn.lpush(user_public_id, order_id)

	redis_conn.close()
	return True


def check_order_id(request, user_data=None, access_rights_check=False):
	if request.method == "POST":
		order_id = request.get_json()['order_id']

	else:
		order_id = request.args.get('order_id', None, str)
		
	redis_conn = redis.Redis()
	redis_loads_data = {}

	if order_id == "all":
		for i in redis_conn.lrange(user_data['public_id'], 0, -1):
			if redis_conn.get(i) is None:
				redis_conn.lrem(user_data['public_id'], 1, i)
				continue
			
			dump = pickle.loads(redis_conn.get(i))
			del dump['qr_url']
			redis_loads_data[i.decode('utf-8')] = dump

		return redis_loads_data


	else:
		redis_data = redis_conn.get(order_id)
		if order_id is None or redis_data is None:
			return None

		redis_loads_data[order_id] = pickle.loads(redis_data)

	if access_rights_check:
		if not redis_loads_data[order_id]['user_public_id'] == user_data['public_id']:
			return None


	redis_conn.close()
	return redis_loads_data[order_id]


def user_data_validation(config, request):
	try:
		rule_dict = config['RULE_DICT'][request.method]
		regex_dict = config['REGEX_DICT']
		rule_hca = config['RULE_HCA'][request.method]
		rule = str(request.url_rule)
		user_data = request.get_json(force=True)

		if rule in rule_hca:
			status_hca = asyncio.run(check_hcaptcha(config['SECRET_KEY_HCA'], user_data['token']))
			if not status_hca:
				return None

		if rule in rule_dict:
			for i in rule_dict[rule]:
				if re.search(regex_dict[i], user_data[i]) is None:
					return None

		return True

	except Exception as e:
		print(e)
		return None


def check_token(session, coin_name, qr_url=None, 
	address=None, check_network = False, network_name=None, get_network_data=False):

	coin_data = session.query(CryptoAddress).filter(CryptoAddress.coin == coin_name).one_or_none()

	if coin_data is None:
		return None

	if check_network:
		check_network_name = session.query(BlockchainNetwork).filter(or_(
			BlockchainNetwork.address == address,
			BlockchainNetwork.qr_url == qr_url)).one_or_none()

		if check_network_name is not None:
			return None

	if get_network_data:
		blockchain_data = session.query(BlockchainNetwork).filter(and_(
			BlockchainNetwork.network_name == network_name,
			BlockchainNetwork.coin_id == coin_data.id)).one_or_none()

		if blockchain_data is not None:
			return coin_data, blockchain_data


	return coin_data


async def check_hcaptcha(secret_key_hca, token):
	async with ClientSession() as session:
		async with session.get(f"https://hcaptcha.com/siteverify?response={token}&secret={secret_key_hca}") as resp:
			respnse = json.loads(await resp.text())
			await session.close()

	return respnse['success']
