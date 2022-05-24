import os
from datetime import timedelta


class Config:
	SECRET_KEY = os.getenv("SECRET_KEY")
	DEBUG = True
	VERSION = "v1"


class TestConfig(Config):
	SQLALCHEMY_DATABASE_URI = "mysql+pymysql://test_user:Sql_-132442@127.0.0.1:3306/test"
	# All Token and Code Expires Times
	JWT_SECRET_KEY = os.getenv("SECRET_KEY")
	ACCESS_EXPIRES = timedelta(minutes = 20)
	REFRESH_EXPIRES = timedelta(days = 3)
	VERIF_EXPIRE = timedelta(minutes = 10)
	JWT_ACCESS_TOKEN_EXPIRES = ACCESS_EXPIRES
	JWT_REFRESH_TOKEN_EXPIRES = REFRESH_EXPIRES
	# Mail Configuration
	MAIL_SERVER = "smtp.gmail.com"
	MAIL_PORT = 465
	MAIL_USE_TLS = True
	MAIL_USERNAME = "naz.abylai50@gmail.com"
	MAIL_PASSWORD = "aveedkprdbobroje"


class ProdConfig(Config):
	SQLALCHEMY_DATABASE_URI = ""
	JWT_SECRET_KEY = ""