from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String, Boolean, Float, Integer, Column, exc
from sqlalchemy.ext.declarative import declarative_base


ballance_base = declarative_base()

class UserBallance(ballance_base):
	__tablename__ = 'user_ballance'

	id = Column(Integer, primary_key = True)
	public_id = Column(String(47), unique = True, nullable = False)
	wallet_id = Column(String(47), unique = True, nullable = False)
	ballance = Column(Float, nullable = False, default = 0.0)
	freeze_status = Column(Boolean, nullable = False, default = False)

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
