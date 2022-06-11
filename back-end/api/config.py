import os
from datetime import timedelta


class Config:
	SECRET_KEY = os.getenv("SECRET_KEY")
	DEBUG = True
	VERSION = "v1"
	SECRET_KEY_HCA = os.getenv("SECRET_KEY_HCA")
	REDIS_URL = os.getenv('REDIS_URL') or 'redis://'

	REGEX_DICT = {"email": "^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$",
		"username": "^[a-zA-Z][a-zA-Z0-9-_.]{1,20}$",
		"password": "^[a-zA-Z][a-zA-Z0-9-_.]{1,40}$",
		"verification_code": "^[0-9]+$"
	}

	RULE_DICT = {
		"POST": {f"/{VERSION}/user/signup": ['email', 'username', 'password'],
				f"/{VERSION}/user/signin": ['email', 'password'],
				f"/{VERSION}/restore/password": ['email', 'password']
		},
		"PATCH":{
			f"/{VERSION}/restore/password": ['verification_code']
		}
	}

	RULE_HCA = {
		"POST": [f"/{VERSION}/user/signup", f"/{VERSION}/user/signin", f"/{VERSION}/restore/password"],
		"PATCH": [f"/{VERSION}/restore/password"]
	}


class TestConfig(Config):
	SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	POOL_SIZE = 20
	# All Token and Code Expires Times
	JWT_SECRET_KEY = os.getenv("SECRET_KEY")
	ACCESS_EXPIRES = timedelta(minutes = 30)
	REFRESH_EXPIRES = timedelta(days = 7)
	VERIF_EXPIRE = timedelta(minutes = 10)
	USER_CONFIRM_EXPIRE = timedelta(hours = 1)
	ADM_CONFIRM_EXPIRE = timedelta(hours = 6)
	JWT_ACCESS_TOKEN_EXPIRES = ACCESS_EXPIRES
	JWT_REFRESH_TOKEN_EXPIRES = REFRESH_EXPIRES
	# Mail Configuration
	MAIL_SERVER = "smtp.gmail.com"
	MAIL_PORT = 465
	MAIL_USE_TLS = True
	MAIL_USERNAME = "naz.abylai50@gmail.com"
	MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")


class ProdConfig(Config):
	SQLALCHEMY_DATABASE_URI = ""
	JWT_SECRET_KEY = ""
