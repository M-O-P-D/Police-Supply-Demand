

from flask import Flask, request, render_template
import json
import io
from io import StringIO
import base64

from dotenv import load_dotenv
load_dotenv()

from crims import model
from crims import visualisation

import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

app = Flask(__name__)


def run_sim(force_name, month):

  year = 2020

  end_year = 2020 if month < 12 else 2021
  end_month = month + 1 if month < 12 else 1

  # construct and run the model for one month only
  microsim = model.CrimeMicrosim(force_name, (year, month), (end_year, end_month))
  model.no.run(microsim)
  return microsim.crimes


from numpy.random import Generator, MT19937
rg = Generator(MT19937(12345))


# test function for netlogo integration
@app.route("/rand", methods=["GET"])
def rand():
  try:
    if not "max" in request.args:
      raise KeyError("max param not specified")
    return json.dumps(rg.random() * float(request.args.get("max"))), 200
  except Exception as e:
    return "%s: %s" % (type(e).__name__, str(e)), 400


@app.route('/data', methods=["GET"])
def crime_data():
  try:
    for p in ["force", "month"]:
      if not p in request.args:
        raise KeyError("param not specified: %s" % p)

    fmt = request.args.get("format", "json") # default to json

    valid_formats = ["json", "csv"]
    if fmt not in valid_formats:
      raise ValueError("format must be one of %s" % str(valid_formats))

    force = request.args.get("force")
    month = int(request.args.get("month"))

    crimes = run_sim(force, month)
    if fmt == "json":
      return json.loads(crimes.sort_values(by="time").to_json(orient="table")), 200
    else:
      csvbuf = StringIO()
      crimes.sort_values(by="time").to_csv(csvbuf)
      return csvbuf.getvalue(), 200

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

if __name__ == "__main__":
  app.run()

