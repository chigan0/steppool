import redis
import pickle
r = redis.Redis()


mydict = {"user_public_id":"dawad-123123dad-ddad","email":"naz.add@gmail.com"}
#p_mydict = pickle.dumps(mydict)
#r.set('mydict',p_mydict,60*5)

#read_dict = r.get('840080')
#yourdict = pickle.loads(read_dict)

#print(yourdict)

a = "hello"

if a is None: 
	print("none")

else:
	print("not none")