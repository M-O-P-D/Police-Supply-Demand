
"""python functions called by netlogo for up/downstream model communication"""


from datetime import date, datetime, timedelta
import pandas as pd
from io import StringIO
from crims.model import CrimeMicrosim

import warnings
# suppress MPI-related warning
warnings.filterwarnings("ignore", category=RuntimeWarning, message="mpi4py module not found, assuming serial mode")
import neworder as no


TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


# model-like wrapper around canned data
class CannedCrimeData(no.Model):
  def __init__(self, start):
    timeline = no.CalendarTimeline(date(start[0], start[1], 1), 1, "m")
    super().__init__(timeline, no.MonteCarlo.deterministic_identical_stream)
    self.crimes = pd.read_csv("./test/crime-sample.csv", parse_dates=["time"], index_col="id")

  def force_area(self):
    return "[canned data]"

  # loading factors do nothing on canned data
  def get_loading(self, _=None):
    return 1.0

  def set_loading(self, _f, _=None):
    pass

  def step(self):
    self.halt()


# init_model must be called to instantiate model
model = None


def set_loading(f, category=None):
  no.log("Setting %s loading to %f" % (category, f))
  return model.set_loading(f, category)


def get_loading(crime_type):
  return model.get_loading(crime_type)


# TODO might be worth passing the ABM timestep size here
def init_model(run_no, force_area, year, month, initial_loading, burn_in):
  global model

  # this adjustment needs to happen on netlogo side to keep dates in sync
  # assert burn_in > 0
  # # adjust year/month so that the supplied values correspond to the *end* of the burn-in period
  # month -= burn_in
  # while month < 1:
  #   year -= 1
  #   month += 12

  # use canned data if requested
  if force_area == "TEST":
    model = CannedCrimeData((year, month))
    return

  # monthly open-ended timeline (run_no is used to seed the mc)
  model = CrimeMicrosim(run_no, force_area, (year, month), burn_in=burn_in)
  no.log("Initialised crime model in %s at %s" % (force_area, model.timeline.time()))
  no.log("MC seed=%d" % model.mc.seed())
  # simulate the first month
  model.set_loading(initial_loading)
  no.run(model)


def get_crimes(start, end):
  global model, timestep

  ts = datetime.strptime(start, TIME_FORMAT)
  te = datetime.strptime(end, TIME_FORMAT)

  # NB model time is the start of the *next* (as yet unsampled) timestep
  if ts >= model.timeline.time():
    no.log("Sampling crimes in %s for month beginning %s..." % (model.force_area(), model.timeline.time()))
    no.run(model)
    no.log("Sampling complete")

  # no.log("%s -> %s: %d" % (ts, te, len(model.crimes[(model.crimes.time >= ts) & (model.crimes.time < te)])))

  buf = StringIO()
  model.crimes[(model.crimes.time >= ts) & (model.crimes.time < te)].to_csv(buf)
  return buf.getvalue()


# test harness
if __name__ == "__main__":

  init_model(0, "Wiltshire", 2020, 1, 1.0, 1)
  # init_canned_data(2020,1)
  print(model.crimes.head())

  model.set_loading(0.1)
  model.set_loading(10.0, "drugs")

  t = model.timeline.start()

  ts = t

  # test time serialisation as it would be if coming from netlogo
  for _ in range(24 * 75):
    te = ts + timedelta(hours=1)
    crimes = pd.read_csv(StringIO(get_crimes(datetime.strftime(ts, TIME_FORMAT), datetime.strftime(te, TIME_FORMAT))), index_col="id")
    no.log("%s->%s: %d crimes" % (ts, te, len(crimes)))
    ts = te

  # print(get_time())
  # crimes = pd.read_csv(StringIO(get_crimes(1.0)), index_col="id")
  # print(crimes.head())
  # print(len(crimes))

  # print(get_time())
  # crimes = pd.read_csv(StringIO(get_crimes(0.5)), index_col="id")
  # print(crimes.head())
  # print(len(crimes))






