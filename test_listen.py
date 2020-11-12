
from flask import Flask, request
import pandas as pd
#import json

app = Flask(__name__)


def get_response(data_in):
  output = pd.DataFrame(index=data_in.groupby(["MSOA", "crime_type"]).indices, columns={"delta": 0.0})
  output.delta = 0.0
  return output


@app.route('/', methods=['POST'])
def result():
  try:
    #print(request.json)  # json (if content-type of application/json is sent with the request)
    data_in = pd.read_json(request.data, orient="table")
    data_out = get_response(data_in)
    print("received %d crimes, sending %d adjustments" % (len(data_in), len(data_out)))
    return data_out.to_json(orient="table"), 200
  except Exception as e:
    return str(e), 400

# data_in = pd.read_csv("./data/crime_sample.csv")
# data_out = get_response(data_in)
# print(type(data_out.to_json(orient="table")))
# print(json.loads(data_out.to_json(orient="table")))