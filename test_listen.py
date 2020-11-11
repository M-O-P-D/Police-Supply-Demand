
from flask import Flask, request
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['POST'])
def result():
  try:
    #print(request.json)  # json (if content-type of application/json is sent with the request)
    df = pd.read_json(request.data, orient="table")
    print("received %d crimes" % len(df))
    print(df.head())
    return "", 200 # could use 202?
  except Exception as e:
    return str(e), 400