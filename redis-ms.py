#redis-srv.py

import redis
import pandas as pd
import pickle
import json
from datetime import date


# v2: microsim model 

# requires non-python dependency redis-server
# sudo apt install redis-server
# follow instructions here: https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-18-04

import neworder as no

class RedisDemoModel(no.Model):
  def __init__(self, force, start_year, start_month, end_year, end_month):
    super().__init__(no.CalendarTimeline(date(start_year, start_month, 1), date(end_year, end_month, 1), 1, "m", 1), no.MonteCarlo.nondeterministic_stream)

    self.force = force
    self.len = 2

    pubsub.subscribe("crime_rate")
    pubsub.subscribe("crime_model_stop")

  def step(self):

    data = pd.DataFrame(data = { "force": [self.force]*self.len, "date": [self.timeline().time()]*self.len, "value": self.mc().ustream(self.len)})

    # send some data
    cache.publish("crime_data", pickle.dumps(data))

    # wait for response...
    for m in pubsub.listen():
      no.log(m)
      if m["type"] == "message" and m["channel"] == b"crime_rate":
        # adjust amount of data to produce accoring to feedback from upstream model
        self.len = json.loads(m["data"])
        break
      if m["type"] == "message" and m["channel"] == b"crime_model_stop":
        self.halt() 


  def checkpoint(self):
    # send done signal (NB (int)0 gets serialised as b"0" i.e. a string (?))
    cache.publish("crime_model_result", json.dumps({"status": 0}))
    pubsub.unsubscribe("crime_rate")

cache = redis.StrictRedis(host='localhost', port=6379)
pubsub = cache.pubsub()
pubsub.subscribe("crime_model_init")

# m = RedisDemoModel("West Yorkshire", 2020, 1, 2021, 1)

# no.run(m)

#def run_model(force, start_year, start_month, duration_months):

while True:
  # list for model init requests
  no.log("waiting for init request")
  for msg in pubsub.listen():
    no.log(msg)
    if msg["type"] == "message" and msg["channel"] == b"crime_model_init":
      params = json.loads(msg["data"])
      model = RedisDemoModel(params["force"], params["start_year"], params["start_month"], params["end_year"], params["end_month"])
      no.run(model)
