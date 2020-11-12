
# %%
import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )


from crims.crime import Crime
import contextily as ctx
import matplotlib.pyplot as plt


crime = Crime('West Yorkshire', 2017, 10, 2020, 9)

gdf = crime.get_neighbourhoods()

ax = gdf.plot(figsize=(10, 10), alpha=0.3, edgecolor='k')
ctx.add_basemap(ax)

# %%

import geopandas as gpd
from shapely.geometry import Point

wypd = crime.api.get_force('west-yorkshire')
crimes = crime.api.get_crimes_area(wypd.get_neighbourhood("BDT_KE").boundary)
#crimes = crime.api.get_crimes_area(wypd.neighbourhoods[0].boundary)

cgdf = gpd.GeoDataFrame({"category": [c.category for c in crimes],
                         "geometry": [Point(float(c.location.longitude), float(c.location.latitude)) for c in crimes]},
                         crs = {"init": "epsg:4326" }).to_crs(epsg=3857)

cgdf.head()
cgdf.plot(ax=ax, color="red", markersize=1)
plt.show()

# %%

counts = crime.get_crime_counts()
print(counts)
outcomes = crime.get_crime_outcomes()
print(outcomes)
cats = crime.get_category_breakdown()
print(cats)

# %%
# import importlib
# importlib.reload(crime.Crime)

# %%


