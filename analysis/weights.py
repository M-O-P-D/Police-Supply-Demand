# %% import numpy as np
import pandas as pd
import requests
from pathlib import Path
import numpy as np

from crims import utils

# see also crime detail from here: https://data.police.uk/static/files/police-uk-category-mappings.csv
# saved to police-uk-category-mappings.csv


cached_data = Path("./data/detailed_offence_weights.csv")

if not cached_data.is_file():
  url = "https://www.ons.gov.uk/file?uri=%2fpeoplepopulationandcommunity%2fcrimeandjustice%2fdatasets%2fcrimeseverityscoreexperimentalstatistics%2fcurrent/cssdatatool.xls"

  response = requests.get(url)
  # read_excel direct from the url gives a 403
  raw = pd.read_excel(response.content, sheet_name="List of weights", header=None, skiprows=5, names=["category", "code", "offence", "weight"]).dropna(how="all")
  raw.category = raw.category.ffill()
  raw = raw[~((raw.code.isna()) & (raw.code.isna()) & (raw.weight.isna()))]
  raw.category = raw.category.apply(lambda s: s.lower())
  # TODO what to do about empty codes (grouping of age/gender, but different weight)?
  # for now just remove
  raw = raw[~raw.code.isna()]
  # remove any duplicated codes
  raw = raw[~raw.duplicated(subset="code")]
  raw.to_csv(cached_data, index=False)
raw = pd.read_csv(cached_data)

print(raw.head())

# duplicate descriptions
dups = raw.groupby("offence").count()
dups = dups[dups.category > 1]
print(dups)

# %%

#print(raw)
print(len(raw)) # 252
print(raw.weight.sum()) # ~140267.55


# # Alex's 2017 processed data
# bd = utils.get_category_subtypes().reset_index()

# bd_desc = bd.description.apply(lambda s: s.lower()).unique()

# raw_desc = raw.offence.apply(lambda s: s.lower()).unique()

# print(len(raw_desc))
# print(len(bd_desc), len(np.intersect1d(bd_desc, raw_desc)),len(np.setdiff1d(bd_desc, raw_desc)))

# %%

cd = utils.get_category_subtypes_WIP().reset_index()

cd_desc = cd.description.apply(lambda s: s.lower()).unique()

print(len(raw_desc))
print(len(cd_desc), len(np.intersect1d(cd_desc, raw_desc)),len(np.setdiff1d(cd_desc, raw_desc)))


# %%


# get unique category-description-code from count data
count_codes = cd.drop(["force", "count", "count_total", "proportion"], axis=1).drop_duplicates()

print("counts has %d unique crimes, %d unique codes, duplicates:" % (len(count_codes), len(count_codes.code_original.unique())))
print(count_codes[count_codes.duplicated(subset="code_original")])
# severity scores
count_codes.to_csv("./code_counts.csv", index=False)

cats_sev = pd.read_csv("./data/detailed_offence_weights.csv")

print("severity has %d unique crimes, %d unique codes" % (len(cats_sev), len(cats_sev.code.unique())))
#print(cats_sev[cats_sev.duplicated(subset="code")])
count_codes = count_codes.merge(cats_sev, left_on="code_severity", right_on="code", suffixes=["_counts", "_severity"])

print("union has %d unique crimes" % len(count_codes))

count_codes.drop("code", axis=1).to_csv("./data/policeuk_code_join.csv", index=False)


# %%
