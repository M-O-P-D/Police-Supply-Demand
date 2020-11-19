
import pandas as pd

from flask import Flask, request, render_template
import json
import io
import base64

from crims import model
from crims import geography
from crims import utils
import neworder as no

import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

from matplotlib import pyplot as plt
from matplotlib.colors import to_rgba
import contextily as ctx

app = Flask(__name__)

no.verbose()

# plot the results on a map
force_boundaries = geography.create_forces_gdf()

all_msoas = geography.get_msoa11_gdf()


def run(force_name, start_year, end_year):
  # construct and run the model
  microsim = model.CrimeMicrosim(start_year, end_year+1, force_name)
  no.run(microsim)
  return microsim.crimes

@app.route('/simulate', methods=['GET'])
def result(): #force, start, end):
  try:

    global force_boundaries
    global msoas

    for p in ["force", "year"]:
      if not p in request.args:
        raise KeyError("param not specified: %s" % p)

    force = request.args.get("force")
    year = int(request.args.get("year"))

    crimes = run(force, year, year)
    crime_counts = crimes[["time"]].groupby(level=0).count().rename({"time": "colour"}, axis=1)

    # shading of MSOAs according to crime counts on a linear scale
    amax = crime_counts["colour"].max()
    # need to deal with rounding errors
    crime_counts["colour"] = crime_counts["colour"].apply(lambda r: to_rgba("r", alpha=min(1.0, 0.1+0.9*r/amax)))
    msoas = pd.merge(all_msoas[all_msoas.MSOA11CD.isin(crime_counts.index.values)][["MSOA11CD", "geometry"]], crime_counts, left_on="MSOA11CD", right_index=True)
    ax = msoas.plot(figsize=(12, 12), color=msoas.colour, edgecolor='k')

    # add force area boundary to map, and background tiles
    force_boundaries[force_boundaries.force == utils.standardise_force_name(force)].plot(ax=ax, facecolor="none", edgecolor='b', linewidth=2)
    ax.set_axis_off()
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
    plt.suptitle("Simulated crime density for %s Police, %d" % (force, year), fontsize=16)
    plt.title("Map tiles by Carto, under CC BY 3.0. Data by OpenStreetMap, under ODbL.", fontsize=12)

    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=120)
    img.seek(0)

    plot_url = base64.b64encode(img.getvalue()).decode()
    return render_template('map.html', plot_url=plot_url)
    #return json.loads(result.sample(frac=0.0001).to_json(orient="table")), 200

  except Exception as e:
    return "%s: %s" % (type(e).__name__, str(e)), 400




