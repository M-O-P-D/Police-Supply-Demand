
import pandas as pd

from flask import Flask, request #, jsonify
import json

from crims import model
import neworder as no

app = Flask(__name__)

no.verbose()

def run(force_name, start_year, end_year):
  # construct and run the model
  microsim = model.CrimeMicrosim(start_year, end_year+1, force_name)
  no.run(microsim)
  return microsim.crimes

@app.route('/simulate', methods=['GET'])
def result(): #force, start, end):
  try:

    for p in ["force", "year"]:
      if not p in request.args:
        raise KeyError("param not specified: %s" % p)

    force = request.args.get("force")
    year = int(request.args.get("year"))

    result = run(force, year, year)
    return json.loads(result.sample(frac=0.0001).to_json(orient="table")), 200

  except Exception as e:
    return "%s: %s" % (type(e).__name__, str(e)), 400




