
""" python functions called by netlogo for downstream model communication """

from io import StringIO
import neworder as no


from crims.model import CrimeMicrosim 


class RandModel(no.Model):
  def __init__(self):
    super().__init__(no.NoTimeline(), no.MonteCarlo.deterministic_identical_stream)

  def step(self):
    pass

  def checkpoint(self):
    pass

rand_model = RandModel()

# test function
def rand(maxval):
  return rand_model.mc().ustream(1)[0] * maxval
  # response = requests.get("http://localhost:5000/rand?max=%f" % float(maxval))
  # if response.status_code == 200:
  #   res = response.json()
  #   return res
  # else:
  #   raise ValueError("error %d: %s" % (response.status_code, response.text))

# init_model must be called to instantiate model
model = None

def init_model(force_area, month):
  global model
  # 1y monthly timeline TODO open-ended...
  model = CrimeMicrosim(2020, month, 2021, month, force_area)
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

  init_model("City of London", 1)

  print(get_time())
  crimes = pd.read_csv(StringIO(get_crimes(1.0)))
  print(crimes.head())
  print(len(crimes))

  print(get_time())
  crimes = pd.read_csv(StringIO(get_crimes(0.5)))
  print(crimes.head())
  print(len(crimes))






