# %%
import neworder as no
from crims import model

#no.verbose()

timeline = no.Timeline(2020,2020,[1])
model = model.CrimeMicrosim(timeline, "west-yorkshire")

# df = model.crime_rates.set_index(["MSOA", "Crime type", "Month"], drop=True)
# print(df)

#no.log(model.crime_rates.loc[("E02001109", "Anti-social behaviour")])

# %%

#print(df.loc[("E02001103", "Anti-social behaviour")])

no.run(model)



# %%
# import importlib
# importlib.reload(model)


# %%
