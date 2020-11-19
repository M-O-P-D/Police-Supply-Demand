import pandas as pd
import neworder as no
import argparse
from crims import model
from crims import geography
from crims import utils

import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

import contextily as ctx
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

def main(force_name, start_year, end_year):

  # construct and run the model
  microsim = model.CrimeMicrosim(start_year, end_year+1, force_name)
  no.run(microsim)

  # plot the results on a map
  force_boundaries = geography.create_forces_gdf()

  msoas = geography.get_msoa11_gdf()
  crime_counts = microsim.crimes[["time"]].groupby(level=0).count().rename({"time": "colour"}, axis=1)

  # shading of MSOAs according to crime counts on a linear scale
  amax = crime_counts["colour"].max()
  # need to deal with rounding errors
  crime_counts["colour"] = crime_counts["colour"].apply(lambda r: to_rgba("r", alpha=min(1.0, 0.1+0.9*r/amax)))
  msoas = pd.merge(msoas[msoas.MSOA11CD.isin(crime_counts.index.values)][["MSOA11CD", "geometry"]], crime_counts, left_on="MSOA11CD", right_index=True)
  ax = msoas.plot(figsize=(10, 10), color=msoas.colour, edgecolor='k')

  # add force area boundary to map, and background tiles
  force_boundaries[force_boundaries.force == utils.standardise_force_name(force_name)].plot(ax=ax, facecolor="none", edgecolor='b', linewidth=2)
  ax.set_axis_off()
  ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
  plt.suptitle("Simulated crime density for %s Police, %d-%d" % (force_name, start_year, end_year), fontsize=16)
  plt.title("Map tiles by Carto, under CC BY 3.0. Data by OpenStreetMap, under ODbL.", fontsize=12)

  plt.show()


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="run crims Microsimualation model")
  parser.add_argument("force_area", type=str, help="the Police Force Area to be simulated")
  parser.add_argument("start_year", type=int, help="the initial year of the simulation (from 1st Jan)")
  parser.add_argument("end_year", type=int, help="the final year of the simulation (to 31 Dec)")
  args = parser.parse_args()

  main(args.force_area, args.start_year, args.end_year)
