
"""python functions called by netlogo for downstream model communication"""

from io import StringIO
from datetime import datetime, timedelta
import neworder as no

from dotenv import load_dotenv
load_dotenv()

from crims.model import CrimeMicrosim

# init_model must be called to instantiate model
model = None
# keep track of the time
time = None
timestep = timedelta(hours=1)

# TODO might be worth passing the ABM timestep size here
def init_model(force_area, year, month):
  global model
  global time
  # monthly open-ended timeline
  model = CrimeMicrosim(force_area, (year, month), agg_mode=False)
  time = model.timeline().time()
  no.log("Initialised crime model in %s at %s" % (force_area, model.timeline().time()))
  # simulate the first month
  get_crimes(1.0)


def get_time():
  global model
  return model.timeline().time().strftime("%Y-%m-%d")

def at_end():
  global model
  return model.timeline().at_end()

# TODO parameter adjustments
def get_crimes(loading):
  global model

  no.log("Setting loading factor to %f" % loading)
  no.log("Sampling crimes in %s for month beginning %s" % (model.force_area(), model.timeline().time()))
  model.set_loading(loading)
  no.run(model)

  buf = StringIO()
  model.crimes.to_csv(buf)
  return buf.getvalue()

def pop_crimes():
  global model, time, timestep

  # TODO this is inefficient
  if time >= model.crimes.time.max():
    no.log("Sampling crimes in %s for month beginning %s" % (model.force_area(), model.timeline().time()))
    no.run(model)

  end = time + timestep

  buf = StringIO()
  model.crimes[(model.crimes.time >= time) & (model.crimes.time < end)].to_csv(buf)
  time = end
  return buf.getvalue()


# test harness
if __name__ == "__main__":

  import pandas as pd

  init_model("City of London", 2020, 1)

  print(model.crimes.head())

  for _ in range(24*45):
    crimes = pd.read_csv(StringIO(pop_crimes()), index_col="id")
    no.log("hour ending %s: %d crimes" % (time, len(crimes)))


  # print(get_time())
  # crimes = pd.read_csv(StringIO(get_crimes(1.0)), index_col="id")
  # print(crimes.head())
  # print(len(crimes))

  # print(get_time())
  # crimes = pd.read_csv(StringIO(get_crimes(0.5)), index_col="id")
  # print(crimes.head())
  # print(len(crimes))






