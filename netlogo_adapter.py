
"""python functions called by netlogo for downstream model communication"""

from io import StringIO
import neworder as no


from crims.model import CrimeMicrosim

# init_model must be called to instantiate model
model = None

def init_model(force_area, year, month):
  global model
  # monthly open-ended timeline
  model = CrimeMicrosim(force_area, (year, month), agg_mode=False)
  no.log("Initialised crime model in %s at %s" % (force_area, model.timeline().time()))


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

# test harness
if __name__ == "__main__":

  import pandas as pd

  init_model("City of London", 2020, 1)

  print(get_time())
  crimes = pd.read_csv(StringIO(get_crimes(1.0)))
  print(crimes.head())
  print(len(crimes))

  print(get_time())
  crimes = pd.read_csv(StringIO(get_crimes(0.5)))
  print(crimes.head())
  print(len(crimes))






