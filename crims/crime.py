#crime.py

import geopandas as gpd
from police_api import PoliceAPI
from shapely.geometry import Polygon, Point

api = PoliceAPI()

# returns a GeoDataFrame
def get_neighbourhoods(force_name):
  forcepd = api.get_force(force_name) # NOT "West Yorkshire Police"

  ns = forcepd.neighbourhoods
  #print(n.locations)# %%

  gdf = gpd.GeoDataFrame({"id": [n.id for n in ns]
                          "name": [n.name for n in ns],
                          "geometry": [Polygon([(p[1], p[0]) for p in n.boundary]) for n in ns]},
                           crs = {"init": "epsg:4326" }).to_crs(epsg=3857)
  return gdf



