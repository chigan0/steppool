from api.resources.user import UserGet, UserSignup, MailConfirm
from api.resources.general import LogOut, UpdateToken, Signin, RestorePass


def setup_routes(api, app):
	api.add_resource(Signin, f"/{app.config['VERSION']}/user/signin", methods=['POST']) # authorization route
	api.add_resource(UserSignup, f"/{app.config['VERSION']}/user/signup", methods=['POST']) # User registration route
	api.add_resource(MailConfirm, f"/{app.config['VERSION']}/user/confirm", methods=['POST']) # authorization route
	api.add_resource(UpdateToken, f"/{app.config['VERSION']}/refresh", methods=['POST']) # Acces Token UPDATATE route
	api.add_resource(LogOut, f"/{app.config['VERSION']}/logout", methods=['DELETE'])
	api.add_resource(UserGet, f"/{app.config['VERSION']}/user/get/<string:user_id>", methods=['GET'])# Get user data route
	api.add_resource(RestorePass, f"/{app.config['VERSION']}/restore/password", methods=['POST', 'PATCH'])