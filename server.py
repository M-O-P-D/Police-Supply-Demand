
import pandas as pd

from flask import Flask, request, render_template
import json
import io
import base64

from crims import model
from crims import geography
from crims import utils
from crims import visualisation


import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

app = Flask(__name__)

#no.verbose()

def run_sim(force_name, month):

  year = 2020
  # construct and run the model
  microsim = model.CrimeMicrosim(year, year+1, force_name)
  model.no.run(microsim)
  return microsim.crimes

@app.route('/data', methods=["GET"])
def crime_data():
  try:
    for p in ["force", "month"]:
      if not p in request.args:
        raise KeyError("param not specified: %s" % p)

    force = request.args.get("force")
    month = int(request.args.get("month"))

    crimes = run_sim(force, month)
    return json.loads(crimes.sort_values(by="time").to_json(orient="table")), 200

  except Exception as e:
    return "%s: %s" % (type(e).__name__, str(e)), 400


@app.route('/map', methods=['GET'])
def crime_map(): #force, start, end):
  try:
    for p in ["force", "month"]:
      if not p in request.args:
        raise KeyError("param not specified: %s" % p)

    force = request.args.get("force")
    month = int(request.args.get("month"))

    crimes = run_sim(force, month)

    plt = visualisation.density_map(crimes, force)

    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=120)
    img.seek(0)

    plot_url = base64.b64encode(img.getvalue()).decode()
    return render_template('map.html', plot_url=plot_url)

  except Exception as e:
    return "%s: %s" % (type(e).__name__, str(e)), 400




