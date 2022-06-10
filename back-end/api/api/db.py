from sqlalchemy import create_engine


def db_connect(config, pool_size): # Connect db function 
	engine = create_engine(config, pool_size = pool_size, pool_recycle=3600)

	return engine


def create_table(engine): # Create table function
	from api.models.user import user_base
	from api.models.crypto_address import crypto_addr_base

	try:
		user_base.metadata.create_all(engine)
		crypto_addr_base.metadata.create_all(engine)

	except Exception as e:
		print(e)
