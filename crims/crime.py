#crime.py

from zipfile import ZipFile
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point
from police_api import PoliceAPI

from .utils import month_range, msoa_from_lsoa

api = PoliceAPI()

# dataset
YEAR=2020
MONTH=5

# returns a GeoDataFrame
def get_neighbourhoods(force_name):
  forcepd = api.get_force(force_name) # NOT "West Yorkshire Police"

  ns = forcepd.neighbourhoods
  #print(n.locations)# %%

  gdf = gpd.GeoDataFrame({"id": [n.id for n in ns],
                          "name": [n.name for n in ns],
                          "geometry": [Polygon([(p[1], p[0]) for p in n.boundary]) for n in ns]},
                           crs = {"init": "epsg:4326" }).to_crs(epsg=3857)
  return gdf

# for now just use bulk downloads
def get_crimes(force_name, start_year, start_month, end_year, end_month):

  z = ZipFile("./cache/2020-05.zip")

  files = ["%s/%s-%s-street.csv" % (d, d, force_name) for d in month_range(start_year, start_month, end_year, end_month)]

  # replace NaNs otherwise data goes missing in groupby operations
  data = pd.concat([pd.read_csv(z.open(f)) for f in files]).fillna("n/a")

  lsoas = data["LSOA code"].unique()

  msoas = msoa_from_lsoa(lsoas)

  data = pd.merge(data, msoas, left_on="LSOA code", right_index=True)

  return data

def get_crime_counts(force_name):

  # get reported crimes
  crimes = get_crimes(force_name, YEAR-3, MONTH+1, YEAR, MONTH)
  
  # assume annual cycle and aggregate years
  crimes.Month = crimes.Month.apply(lambda ym: ym.split("-")[1])

  # TODO sample annual variability? 3 counts will give *some* indication?

  # count monthly incidence by time, space and type. note this is an *annual* incidence rate
  counts = crimes[["MSOA", "Crime type", "Month", "Crime ID"]] \
    .rename({"Crime ID": "count"}, axis=1) \
    .groupby(["MSOA", "Month", "Crime type"]) \
    .count() \
    .unstack(level=1, fill_value=0) #.reset_index()
  
  # ensure all data accounted for
  assert counts.sum().sum() == len(crimes)

  # counts["count"] = counts["count"].astype(float) * 12 / 3
  counts = counts.astype(float) * 12 / 3

  # the incidences are the lambdas for sampling arrival times
  return counts

# aggregated outcomes per category
def get_crime_outcomes(force_name):

  # get reported crimes
  crimes = get_crimes(force_name, YEAR-3, MONTH+1, YEAR, MONTH)

  print(len(crimes), len(crimes["Crime ID"]))

  outcomes = crimes[["Crime type", "Last outcome category", "Crime ID"]] \
    .rename({"Crime ID": "count"}, axis=1) \
    .groupby(["Crime type", "Last outcome category"]) \
    .count()

  # ensure all data accounted for
  assert outcomes["count"].sum() == len(crimes)

  # normalise
  outcomes = pd.merge(outcomes, outcomes.groupby(level=0).sum(), left_index=True, right_index=True, suffixes=("", "_total"))

  # normalise

  outcomes["weight"] = outcomes["count"] / outcomes["count_total"]

  print(outcomes)

  return outcomes
