
import pandas as pd
import requests

class DataStream:
  __headers = {'content-type': 'application/json'}

  def __init__(self, url):
    self.url = url

  def send(self, dataframe):
    try:
      json_data = dataframe.to_json(orient="table")
      response = requests.post(self.url, data=json_data, headers=DataStream.__headers)
      if response.status_code == 200:
        return True
    except Exception as e:
      print(e)
    return False

