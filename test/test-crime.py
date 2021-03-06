
# %%
# import warnings
# warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj')


import neworder as no
from crims.crime import Crime

crime = Crime('West Yorkshire', 3, 2021, 2)

# police-api-client seems to be broken

# gdf = crime.get_neighbourhoods()

# ax = gdf.plot(figsize=(10, 10), alpha=0.3, edgecolor='k')
# ctx.add_basemap(ax)

# %%

# import geopandas as gpd
# from shapely.geometry import Point

# wypd = crime.api.get_force('west-yorkshire')
# crimes = crime.api.get_crimes_area(wypd.get_neighbourhood("BDT_KE").boundary)
# #crimes = crime.api.get_crimes_area(wypd.neighbourhoods[0].boundary)

# cgdf = gpd.GeoDataFrame({"category": [c.category for c in crimes],
#                          "geometry": [Point(float(c.location.longitude), float(c.location.latitude)) for c in crimes]},
#                          crs = {"init": "epsg:4326" }).to_crs(epsg=3857)

# cgdf.head()
# cgdf.plot(ax=ax, color="red", markersize=1)
# plt.show()

# %%

counts = crime.get_crime_counts()
print(counts.sum(axis=1))
print(counts.sum(axis=1).sum())


outcomes = crime.get_crime_outcomes()
print(outcomes)
cats = crime.get_category_breakdown()
print(cats)

subcats = cats.loc["violence and sexual offences"]
print(subcats)
print(subcats.proportion.sum())

d = subcats.index.values
p = subcats.proportion.values

m = no.Model(no.NoTimeline(), no.MonteCarlo.deterministic_identical_stream)
print("%g" % (subcats.proportion.sum() - 1.0))
s = m.mc.sample(100, subcats.proportion.values/subcats.proportion.sum())
print(subcats.iloc[s].index)

print(counts.index.levels[1].unique())
print(cats.index.unique())
# %%
# import importlib
# importlib.reload(crime.Crime)

# %%


