#crime.py

from zipfile import ZipFile
from pathlib import Path
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point
from police_api import PoliceAPI

from .utils import month_range, msoa_from_lsoa

class Crime:

  __outcomes_mapping = { 
    'Action to be taken by another organisation': False, 
    'Awaiting court outcome': True,
    'Court case unable to proceed': True, 
    'Court result unavailable': True,
    'Defendant found not guilty': True,
    'Defendant sent to Crown Court': True,
    'Formal action is not in the public interest': False,
    'Further action is not in the public interest': False,
    'Further investigation is not in the public interest': False,
    'Investigation complete; no suspect identified': False, 
    'Local resolution': False,
    'Offender deprived of property': True, 
    'Offender fined': True,
    'Offender given a caution': True, 
    'Offender given a drugs possession warning': True,
    'Offender given absolute discharge': True,
    'Offender given community sentence': True,
    'Offender given conditional discharge': True, 
    'Offender given penalty notice': True,
    'Offender given suspended prison sentence': True,
    'Offender ordered to pay compensation': True, 
    'Offender otherwise dealt with': True,
    'Offender sent to prison': True, 
    'Status update unavailable': False,
    'Suspect charged as part of another case': True,
    'Unable to prosecute suspect': True, 
    'Under investigation': False, 
    'n/a': False  
  }


  # TODO this breaks if not a whole number of years
  """ Class to hold raw crime data and process it as necessary. The dataset is large so loading it is expensive """
  def __init__(self, force_name, start_year, start_month, end_year, end_month):

    # self.year = year
    # self.month = month
    self.force_name = force_name.lower().replace(" ", "-") # "West Yorkshire" -> "west-yorkshire"
    self.api = PoliceAPI()
    self.data = Crime.__get_raw_data(self.force_name, start_year, start_month, end_year, end_month)
    self.data["SuspectDemand"] = self.data["Last outcome category"].apply(lambda c: Crime.__outcomes_mapping[c])
    # assume annual cycle and aggregate years
    self.data["MonthOnly"] = self.data.Month.apply(lambda ym: ym.split("-")[1])

  # returns a GeoDataFrame
  def get_neighbourhoods(self, force_name=None):
    # allow getting neighbourhoods from another force (without having to load all the crime data)
    if force_name is None:
      force_name = self.force_name
    forcepd = self.api.get_force(force_name) 

    ns = forcepd.neighbourhoods
    #print(n.locations)# %%

    gdf = gpd.GeoDataFrame({"id": [n.id for n in ns],
                            "name": [n.name for n in ns],
                            "geometry": [Polygon([(p[1], p[0]) for p in n.boundary]) for n in ns]},
                            crs = {"init": "epsg:4326" }).to_crs(epsg=3857)
    return gdf

  # for now just use bulk downloads
  @staticmethod
  def __get_raw_data(force_name, start_year, start_month, end_year, end_month):

    file = "%d-%02d.zip" % (end_year, end_month)

    local_file = Path("./cache/%s" % file)

    if not local_file.is_file():
      print("Data not found locally, downloading...")
      r = requests.get("https://data.police.uk/data/archive/%s" % file)
      open(local_file , 'wb').write(r.content)
      print("...saved to %s", local_file)
    
    z = ZipFile(local_file)

    files = ["%s/%s-%s-street.csv" % (d, d, force_name) for d in month_range(start_year, start_month, end_year, end_month)]

    # replace NaNs otherwise data goes missing in groupby operations
    data = pd.concat([pd.read_csv(z.open(f)) for f in files]).fillna("n/a")
    msoas = msoa_from_lsoa(data["LSOA code"].unique())

    return pd.merge(data, msoas, left_on="LSOA code", right_index=True)

  def get_crime_counts(self):

    # TODO sample annual variability? 3 counts will give *some* indication?

    # count monthly incidence by time, space and type. note this is an *annual* incidence rate
    counts = self.data[["MSOA", "Crime type", "MonthOnly", "Crime ID"]] \
      .rename({"Crime ID": "count"}, axis=1) \
      .groupby(["MSOA", "MonthOnly", "Crime type"]) \
      .count() \
      .unstack(level=1, fill_value=0) #.reset_index()
    
    # ensure all data accounted for
    assert counts.sum().sum() == len(self.data)

    # counts["count"] = counts["count"].astype(float) * 12 / 3
    counts = counts.astype(float) * 12 / 3

    # the incidences are the lambdas for sampling arrival times
    return counts

  # aggregated outcomes per category TODO add geography?
  def get_crime_outcomes(self):

    # get reported crimes

    outcomes = self.data[["Crime type", "SuspectDemand", "Crime ID"]] \
      .rename({"Crime ID": "count"}, axis=1) \
      .groupby(["Crime type", "SuspectDemand"]) \
      .count()

    # ensure all data accounted for
    assert outcomes["count"].sum() == len(self.data)

    # normalise
    outcomes = pd.merge(outcomes, outcomes.groupby(level=0).sum(), left_index=True, right_index=True, suffixes=("", "_total"))
    outcomes["weight"] = outcomes["count"] / outcomes["count_total"]

    return outcomes
