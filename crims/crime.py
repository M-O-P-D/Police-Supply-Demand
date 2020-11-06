#crime.py

from zipfile import ZipFile
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point
from police_api import PoliceAPI

from .utils import month_range, msoa_from_lsoa

api = PoliceAPI()

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

  data = pd.concat([pd.read_csv(z.open(f)) for f in files])

  lsoas = data["LSOA code"].unique()

  msoas = msoa_from_lsoa(lsoas)

  data = pd.merge(data, msoas, left_on="LSOA code", right_index=True)

  return data



