
"""python functions called by netlogo for up/downstream model communication"""

from datetime import date


import warnings
# suppress MPI-related warning
warnings.filterwarnings("ignore", category=RuntimeWarning, message="mpi4py module not found, assuming serial mode")

from io import StringIO
from datetime import datetime, timedelta
import neworder as no

from crims.model import CrimeMicrosim

# model-like wrapper around canned data
class CannedCrimeData(no.Model):
  def __init__(self, start):
    timeline = no.CalendarTimeline(date(start[0], start[1], 1), 1, "m")
    super().__init__(timeline, no.MonteCarlo.deterministic_identical_stream)
    self.crimes = pd.read_csv("./data/crime-sample.csv", parse_dates=["time"])

  def step(self):
    pass

# init_model must be called to instantiate model
model = None
# keep track of the time
time = None
timestep = timedelta(hours=1)


def set_loading(f, category=None):
  return model.set_loading(f, category)

def get_loading():
  return model.get_loading()


def init_canned_data(year, month):
  global model
  global time

  # monthly open-ended timeline
  model = CannedCrimeData((year, month))
  time = model.timeline().time()


# TODO might be worth passing the ABM timestep size here
def init_model(run_no, force_area, year, month, initial_loading=1.0):
  global model
  global time

  # monthly open-ended timeline (run_no is used to seed the mc)
  model = CrimeMicrosim(run_no, force_area, (year, month), agg_mode=False)
  time = model.timeline().time()
  no.log("Initialised crime model in %s at %s" % (force_area, model.timeline().time()))
  no.log("MC seed=%d" % model.mc().seed())
  # simulate the first month
  model.set_loading(initial_loading)
  no.run(model)


def get_time():
  #global model
  return model.timeline().time().strftime("%Y-%m-%d")

def at_end():
  #global model
  return model.timeline().at_end()

# # TODO parameter adjustments
# def get_crimes(loading):
#   global model

#   no.log("Setting loading factor to %f" % loading)
#   no.log("Sampling crimes in %s for month beginning %s" % (model.force_area(), model.timeline().time()))
#   model.set_loading(loading)
#   no.run(model)

#   buf = StringIO()
#   model.crimes.to_csv(buf)
#   return buf.getvalue()

# TODO #6 time window arguments
def get_crimes():
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

  init_model(0, "City of London", 2020, 1)
  #init_canned_data(2020,1)
  print(model.crimes.head())

  model.set_loading(0.1)
  model.set_loading(10.0, "drugs")

  for _ in range(24*45):
    crimes = pd.read_csv(StringIO(get_crimes()), index_col="id")
    no.log("hour ending %s: %d crimes" % (time, len(crimes)))

  print(model.get_loading())


  # print(get_time())
  # crimes = pd.read_csv(StringIO(get_crimes(1.0)), index_col="id")
  # print(crimes.head())
  # print(len(crimes))

  # print(get_time())
  # crimes = pd.read_csv(StringIO(get_crimes(0.5)), index_col="id")
  # print(crimes.head())
  # print(len(crimes))






