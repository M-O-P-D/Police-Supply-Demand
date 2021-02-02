# %%
import neworder as no
from crims import model

import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

no.verbose()

start_year = 2020
end_year = 2021
#force = "West Yorkshire"
force = "City of London"

model = model.CrimeMicrosim(force, (start_year, 1), (end_year, 1))

#no.log(model.crime_rates.loc[("E02001109", "Anti-social behaviour")])

# %%

#print(df.loc[("E02001103", "Anti-social behaviour")])

no.run(model)

# model.crimes.sample(frac=0.001).to_csv("./data/crime_sample.csv")
#print(model.crimes.sample(10))


# %%
# import importlib
# importlib.reload(model)


# %%
