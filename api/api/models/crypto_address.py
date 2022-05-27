from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Column, DateTime, exc
from sqlalchemy.ext.declarative import declarative_base


crypto_addr_base = declarative_base()

class CryptoAddress(crypto_addr_base):
	__tablename__ = 'crypto_address'

	id = Column(Integer, primary_key = True)
	coin = Column(String(60), unique = True)
	address = Column(String(360), unique = True)
	qr_url = Column(String(516), unique = True, nullable = True)
	create_date = Column(DateTime(), default = datetime.now)


	def save_to_db(self, session):
		try:
			session.add(self)
			session.commit()

		except exc.SQLAlchemyError as e:
			session.rollback()


	def delete_from_db(self, session):
		session.delete(self)
		session.commit()


	def serialize(self):
		return {self.coin: self.address}


	def elem(self):
		return self.coin, self.address, self.qr_url