from api.resources.action_user import UserSignup, MailConfirm, ReplenishBalans
from api.resources.general import UpdateToken, Signin, RestorePass, GetCoin
from api.resources.admin import CoinAddress, ConfirmTransaction


def setup_routes(api, app, api_version):
	api.add_resource(Signin, f"/{api_version}/user/signin", methods = ['POST']) # authorization route
	api.add_resource(UserSignup, f"/{api_version}/user/signup", methods = ['POST']) # User registration route
	api.add_resource(MailConfirm, f"/{api_version}/user/confirm", methods = ['POST']) # Confirm EMAIL
	api.add_resource(UpdateToken, f"/{api_version}/refresh", methods = ['POST', 'DELETE']) # Acces Token UPDATATE route
	api.add_resource(RestorePass, f"/{api_version}/restore/password", methods = ['POST', 'PATCH']) # Restore Password
	api.add_resource(CoinAddress, f"/{api_version}/coin/list", methods = ['POST', 'GET', 'PATCH', 'PUT']) # Crypto addres
	api.add_resource(GetCoin, f"/{api_version}/coin/get/<string:coin_name>", methods = ['GET'])
	api.add_resource(ReplenishBalans, f"/{api_version}/pay", methods = ['GET', 'POST', 'PATCH', 'DELETE'])
	api.add_resource(ConfirmTransaction, f"/{api_version}/admin/pay", methods = ['GET', 'POST', 'PATCH']) # Admin confrimt Transaction
