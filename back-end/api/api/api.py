from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from redis import StrictRedis, Redis, ConnectionPool
from rq import Queue

from config import Config, TestConfig, ProdConfig
from api.db import db_connect, create_table
from api.router import setup_routes

def create_app():
	app = Flask(__name__)
	app.config.from_object(TestConfig if Config.DEBUG else ProdConfig)
	api = Api(app,)
	jwt = JWTManager(app)
	engine = db_connect(app.config['SQLALCHEMY_DATABASE_URI'], app.config['POOL_SIZE'])
	jwt_redis_blocklist = StrictRedis(decode_responses = True)
	
	app.config['jwt_redis_blocklist'] = jwt_redis_blocklist
	
	app.engine = engine
	app.redis_pool = ConnectionPool()
	app.task_queue = Queue('steppool-tasks', connection=Redis(connection_pool=app.redis_pool))

	CORS(app, resources={f"/{app.config['VERSION']}/*": {"origins": "*"}})
	create_table(engine) # function to create a table User
	setup_routes(api, app, app.config['VERSION'])

	@jwt.token_in_blocklist_loader
	def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
		jti = jwt_payload["jti"]
		token_in_redis = jwt_redis_blocklist.get(jti)
		return token_in_redis is not None

	return app
