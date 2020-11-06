
# %%

from crims import crime
import contextily as ctx

gdf = crime.get_neighbourhoods('west-yorkshire')

ax = gdf.plot(figsize=(10, 10), alpha=0.3, edgecolor='k')
ctx.add_basemap(ax)

# %%
import geopandas as gpd
from shapely.geometry import Point

wypd = crime.api.get_force('west-yorkshire')
#crimes = crime.api.get_crimes_area(wypd.get_neighbourhood("BDT_KE").boundary)
crimes = crime.api.get_crimes_area(wypd.neighbourhoods[0].boundary)

cgdf = gpd.GeoDataFrame({"category": [c.category for c in crimes],
                         "geometry": [Point(float(c.location.longitude), float(c.location.latitude)) for c in crimes]},
                         crs = {"init": "epsg:4326" }).to_crs(epsg=3857)

cgdf.head()
#cgdf.plot(ax=ax, color="red")
# %%

import pandas as pd

force_name = "west-yorkshire"
year = 2020
month = 5

crimes = crime.get_crimes(force_name, year-1, month, year, month)

print(crimes.Month.unique())
print(crimes.columns.values)
print(crimes.head())

# %%

import importlib
importlib.reload(crims)
