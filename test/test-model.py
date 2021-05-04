# %%
import pandas as pd
import neworder as no
from crims import model

import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

#no.verbose()

start = (2021, 1)
end = (2022, 1)
#force = "West Yorkshire"
#force = "Durham"
force = "City of London"

model = model.CrimeMicrosim(0, force, start, end)

#no.log(model.crime_rates.loc[("E02001109", "Anti-social behaviour")])

# %%

#print(df.loc[("E02001103", "Anti-social behaviour")])

no.run(model)
# 1 year of data (no burn-in)
print(model.crimes)

category_summary = model.crimes[["crime_category", "MSOA"]].groupby("crime_category").count()

# compare simulated counts with bulk data
category_counts = model.get_input().groupby("crime_type").sum().T.mean()

comp = pd.concat([category_summary, category_counts], axis=1).rename({"MSOA": "simulated", 0: "observed"}, axis=1)
comp["rel_diff"] = comp.simulated / comp.observed - 1.0
print(comp)
print(comp.sum())

area_summary = model.crimes[["code", "MSOA"]].groupby("MSOA").count()
area_counts = model.get_input().groupby("MSOA").sum().T.mean()

comp = pd.concat([area_summary, area_counts], axis=1).rename({"code": "simulated", 0: "observed"}, axis=1).fillna(0)
comp["rel_diff"] = comp.simulated / comp.observed - 1.0
print(comp)
print(comp.sum())


# model.set_loading(1.35, "drugs")
# model.set_loading(0.65, "burglary")
# no.run(model)
# # should be 1 month of data
# print(model.crimes)

# no.run(model)
# # should be 1 month of data
# print(model.crimes)

# no.run(model)
# # should be 1 month of data
# print(model.crimes)

# #model.crimes.sample(n=500).sort_values(by="time").to_csv("./test/crime-sample.csv")
# print(model.crimes.sample(10))


# %%
# import importlib
# importlib.reload(model)


# %%
