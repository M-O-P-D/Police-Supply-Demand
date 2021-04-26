# %%
import neworder as no
from crims import model

import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

#no.verbose()

start = (2021, 1)
end = (2021, 12)
#force = "West Yorkshire"
#force = "Durham"
force = "City of London"

model = model.CrimeMicrosim(0, force, start, end)

#no.log(model.crime_rates.loc[("E02001109", "Anti-social behaviour")])

# %%

#print(df.loc[("E02001103", "Anti-social behaviour")])

no.run(model)
# should be burn-in period worth of data
print(model.crimes)


model.set_loading(1.35, "drugs")
model.set_loading(0.65, "burglary")
no.run(model)
# should be 1 month of data
print(model.crimes)

no.run(model)
# should be 1 month of data
print(model.crimes)

no.run(model)
# should be 1 month of data
print(model.crimes)

#model.crimes.sample(n=500).sort_values(by="time").to_csv("./test/crime-sample.csv")
print(model.crimes.sample(10))


# %%
# import importlib
# importlib.reload(model)


# %%
