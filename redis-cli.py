# redis-cli.py

import redis
import pickle
import pandas as pd
from time import sleep
import json

cache = redis.StrictRedis(host='localhost', port=6379)
pubsub = cache.pubsub()

# requires non-python dependency redis-server
# sudo apt install redis-server
# follow instructions here: https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-18-04

# request a model run
cache.publish("crime_model_init", json.dumps({"force": "West Yorkshire", "start_year": 2020, "start_month": 1, "end_year": 2021, "end_month": 1}))

# now listen for incoming data
pubsub.subscribe("crime_data") # monthly crimes
pubsub.subscribe("crime_model_result") # model finished

# listen for incoming data
for m in pubsub.listen():
  if m["type"] == "message" and m["channel"] == b'crime_data':
    # process it
    df = pickle.loads(m["data"])
    print(df.head())
    #sleep(1)
    # send response
    cache.publish("crime_rate", 2 + int(df.value.sum()))
  elif m["type"] == "message" and m["channel"] == b'crime_model_result':
    print("model status: %d" % json.loads(m["data"])["status"])
    break
  else:
    print(m)

