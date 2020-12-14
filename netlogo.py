
""" python functions called by netlogo for downstream model communication """

from io import StringIO
#import requests
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


# TODO once resume functionality is implemented, make the model persistent
# TODO parameter adjustments
def model(force_area, month):
  end_year = 2020
  end_month = month + 1
  if end_month == 13:
    end_year += 1
    end_month = 1

  no.log("Sampling crimes in %s for 2020/%d" % (force_area, month))
  m = CrimeMicrosim(2020, month, end_year, end_month, force_area)
  no.run(m)

  buf = StringIO()
  m.crimes.to_csv(buf)
  return buf.getvalue()

if __name__ == "__main__":
  print(model("City of London", 1))


