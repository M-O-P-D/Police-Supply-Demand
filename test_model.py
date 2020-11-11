# %%
import pandas as pd
import neworder as no
from crims import model
from crims import geography

import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

import contextily as ctx
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

#no.verbose()

start_year = 2020
end_year = 2022
force = "west-yorkshire"
#force = "city-of-london"

model = model.CrimeMicrosim(start_year, end_year, force)

# df = model.crime_rates.set_index(["MSOA", "Crime type", "Month"], drop=True)
# print(df)

#no.log(model.crime_rates.loc[("E02001109", "Anti-social behaviour")])

# %%

#print(df.loc[("E02001103", "Anti-social behaviour")])

no.run(model)

force_boundaries = geography.create_forces_gdf()

msoas = geography.get_msoa11_gdf()

crime_counts = model.crimes[["time"]].groupby(level=0).count().rename({"time": "colour"}, axis=1)

# log scale
# amax = np.log(crime_counts["colour"].max())
# crime_counts["colour"] = crime_counts["colour"].apply(lambda r: to_rgba("r", alpha=0.1+0.9*np.log(r)/amax))
# linear scale
amax = crime_counts["colour"].max()
# need to deal with rounding errors
crime_counts["colour"] = crime_counts["colour"].apply(lambda r: to_rgba("r", alpha=min(1.0, 0.1+0.9*r/amax)))

msoas = pd.merge(msoas[msoas.MSOA11CD.isin(crime_counts.index.values)][["MSOA11CD", "geometry"]], crime_counts, left_on="MSOA11CD", right_index=True)

ax = msoas.plot(figsize=(10, 10), color=msoas.colour, edgecolor='k')
force_boundaries[force_boundaries.force == force].plot(ax=ax, facecolor="none", edgecolor='b', linewidth=2)
ax.set_axis_off()
# ctx.providers.keys()
# dict_keys(['OpenStreetMap', 'OpenSeaMap', 'OpenPtMap', 'OpenTopoMap', 'OpenRailwayMap', 'OpenFireMap', 'SafeCast', 'Thunderforest', 'OpenMapSurfer', 'Hydda', 'MapBox', 'Stamen', 'Esri', 'OpenWeatherMap', 'HERE', 'FreeMapSK', 'MtbMap', 'CartoDB', 'HikeBike', 'BasemapAT', 'nlmaps', 'NASAGIBS', 'NLS', 'JusticeMap', 'Wikimedia', 'GeoportailFrance', 'OneMapSG'])
# ctx.providers.CartoDB.keys()...
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

plt.suptitle("Map tiles by Carto, under CC BY 3.0. Data by OpenStreetMap, under ODbL.")

plt.show()

model.crimes.sample(frac=0.001).to_csv("./data/crime_sample.csv")



# %%
# import importlib
# importlib.reload(model)


# %%
