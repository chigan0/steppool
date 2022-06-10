from datetime import datetime

from sqlalchemy import Integer, String, Column, DateTime, exc, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base


crypto_addr_base = declarative_base()

class CryptoAddress(crypto_addr_base):
	__tablename__ = 'crypto_address'
	id = Column(Integer, primary_key = True)
	coin = Column(String(60), unique = True)
	create_date = Column(DateTime(), default = datetime.now)


	def save_to_db(self, session):
		try:
			session.add(self)
			session.commit()

		except exc.SQLAlchemyError as e:
			print(e)
			session.rollback()


	def delete_from_db(self, session):
		session.delete(self)
		session.commit()


	def elem(self):
		return self.id, self.coin


class BlockchainNetwork(crypto_addr_base):
	__tablename__ = 'blockchain_network'
	id = Column(Integer, primary_key = True)

	coin_id = Column(Integer(), ForeignKey('crypto_address.id'), unique = False)
	network_name = Column(String(60), unique = False)
	address = Column(String(360), unique = True)
	qr_url = Column(String(516), unique = True, nullable = True)


	def save_to_db(self, session):
		try:
			session.add(self)
			session.commit()

		except exc.SQLAlchemyError as e:
			print(e)
			session.rollback()


	def serialize(self):
		return self.network_name, self.address, self.qr_url


	def serialize_json(self):
		return {"network_name": self.network_name, "address": self.address, "qr_url": self.qr_url}