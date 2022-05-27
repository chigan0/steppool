from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from config import TestConfig


def db_connect(config, pool_size): # Connect db function 
	engine = create_engine(config, pool_size = pool_size, pool_recycle=3600)

	return engine.begin()


def create_table(engine): # Create table function
	from api.models.user import User, user_base
	from api.models.crypto_address import CryptoAddress, crypto_addr_base
	from api.models.balance import UserBallance, ballance_base

	user_base.metadata.create_all(engine)
	crypto_addr_base.metadata.create_all(engine)
	ballance_base.metadata.create_all(engine)
