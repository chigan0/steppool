from rq import Queue
from redis import Redis
from task import count_words_at_url
import time

# Tell RQ what Redis connection to use
redis_conn = Redis()
q = Queue(connection=redis_conn)  # no args implies the default queue

# Delay execution of count_words_at_url('http://nvie.com')
job = q.enqueue(count_words_at_url, 'http://nvie.com')
print(job.result)   # => None

# Now, wait a while, until the worker is finished
time.sleep(3)
print(job.result)   # => 889