# %%

import pandas as pd

file = "../crime_sim_toolkit/crime_sim_toolkit/src/prc-pfa-201718_new.csv"

raw = pd.read_csv(file)

print(len(raw.Offence_Description.unique()))

cats = raw.groupby(["Force_Name", "Policeuk_Cat", "Offence_Description"]).sum() \
  .drop(["Unnamed: 0", "Financial_Quarter"], axis=1) \
  .rename({"Number_of_Offences": "offences"}, axis=1)

cat_totals = cats.groupby(level=[0,1]).sum()

print(cats.head())
print(cat_totals.head())

cats = pd.merge(cats, cat_totals, left_index=True, right_index=True, suffixes=["", "_cat"])
cats["proportion"] = cats.offences / cats.offences_cat
print(cats.head())

# %%
