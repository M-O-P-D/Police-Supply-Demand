import pandas as pd
import requests

data = pd.read_csv("./data/crime_sample.csv").set_index(["MSOA", "crime_type"], drop=True)

print(len(data))

print(data)


headers = {'content-type': 'application/json'}
json_data = data.to_json(orient="table")

url="http://localhost:5000/"

try:
  response = requests.post(url,data=json_data, headers=headers)
  if response.status_code == 200:
    print("sent")
  else:
    print(response.text)
except Exception as e:
  print(e)
