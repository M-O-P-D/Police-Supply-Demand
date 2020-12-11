
""" python functions called by netlogo for downstream model communication """

import requests

# test function
def rand(maxval):
  response = requests.get("http://localhost:5000/rand?max=%f" % float(maxval))
  if response.status_code == 200:
    res = response.json()
    return res
  else:
    raise ValueError("error %d: %s" % (response.status_code, response.text))


