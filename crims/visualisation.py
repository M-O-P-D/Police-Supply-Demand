

import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import contextily as ctx

from dotenv import load_dotenv
load_dotenv()

from . import geography
from .utils import standardise_force_name

force_boundaries = geography.create_forces_gdf()

all_msoas = geography.get_msoa11_gdf()


def density_map(crimes, force_name):
  # plot the results on a map
  crime_counts = crimes[["MSOA", "time"]].groupby("MSOA").count().rename({"time": "colour"}, axis=1)

  print(crime_counts)

  crimes["time"] = pd.to_datetime(crimes["time"], format="%Y-%m-%d %H:%M:%S")
  start = min(crimes["time"])
  end = max(crimes["time"])

  print(crimes.info())
  print(crimes["time"].dtype)

  # shading of MSOAs according to crime counts on a linear scale
  amax = crime_counts["colour"].max()
  # need to deal with rounding errors
  crime_counts["colour"] = crime_counts["colour"].apply(lambda r: to_rgba("r", alpha=min(1.0, 0.1+0.9*r/amax)))
  msoas = pd.merge(all_msoas[all_msoas.MSOA11CD.isin(crime_counts.index.values)][["MSOA11CD", "geometry"]], crime_counts, left_on="MSOA11CD", right_index=True)
  ax = msoas.plot(figsize=(10, 10), color=msoas.colour, edgecolor='k')

  # add force area boundary to map, and background tiles
  force_boundaries[force_boundaries.force == standardise_force_name(force_name)].plot(ax=ax, facecolor="none", edgecolor='b', linewidth=2)
  ax.set_axis_off()
  ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
  period = "%d/%d" % (start.year, start.month) if start.year == end.year and start.month == end.month else "%d/%d - %d/%d" % (start.year, start.month, end.year, end.month)
  plt.title("Simulated crime density for %s Police, %s" % (force_name, period) , fontsize=14)

  return plt
