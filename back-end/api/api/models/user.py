from hashlib import pbkdf2_hmac
from json import dumps
from datetime import datetime

from sqlalchemy import Integer, String, Column, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from flask_jwt_extended import create_access_token, create_refresh_token


user_base = declarative_base()

class User(user_base):# User model
    __tablename__ = "users"
    
    id = Column(Integer, primary_key = True)
    public_id = Column(String(37), unique = True, nullable = False)
    email = Column(String(70), unique = True, nullable = False)
    username = Column(String(60), unique = True, nullable = False)
    password_hash = Column(String(168), unique = False, nullable = False)
    role = Column(String(36), unique = False, default = 'user')
    status = Column(String(36), unique = False, default = 'offline')
    create_date = Column(DateTime(), default = datetime.now)

    def set_password_hash(self, password, salt):
        key = pbkdf2_hmac('sha256', password.encode('utf-8'),salt.encode('utf-8'), 100000)
        self.password_hash = key.hex()

    @property
    def serialize(self):
        return {
            'public_id': self.public_id,
            'email': self.email,
            'username': self.username,
            'role': self.role,
            'status': self.status,
            'create_date': dumps(self.create_date, default=str)
        }
    
    def save_to_db(self, session):
        try:
            session.add(self)
            session.commit()

        except exc.SQLAlchemyError as e:
            session.rollback()


    def create_jwt_token(self,):
        access_token = create_access_token(identity={
            'role': self.role,
            'public_id': self.public_id,
            "email": self.email,
            "username": self.username,
            "create_date": dumps(self.create_date, default=str)
        })

        refresh_token = create_refresh_token(identity = {"public_id": self.public_id})
        return access_token, refresh_token


class UserBallance(user_base):
    __tablename__ = 'user_ballance'

    id = Column(Integer, primary_key = True)
    public_id = Column(String(64), unique = True)
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
