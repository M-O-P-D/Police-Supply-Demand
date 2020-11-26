import numpy as np
import pandas as pd
import requests
from pathlib import Path

from crims import utils

cached_data = Path("./data/detailed_offence_weights.csv")

if not cached_data.is_file():
  url = "https://www.ons.gov.uk/file?uri=%2fpeoplepopulationandcommunity%2fcrimeandjustice%2fdatasets%2fcrimeseverityscoreexperimentalstatistics%2fcurrent/cssdatatool.xls"

  response = requests.get(url)
  # read_excel direct from the url gives a 403
  raw = pd.read_excel(response.content, sheet_name="List of weights", header=None, skiprows=5, names=["category", "code", "offence", "weight"]).dropna(how="all")
  raw = raw[~((raw.code.isna()) & (raw.code.isna()) & (raw.weight.isna()))]
  raw.category = raw.category.ffill()
  raw.to_csv(cached_data, index=False)
raw = pd.read_csv(cached_data)

#print(raw)
print(len(raw)) # 252
print(raw.weight.sum()) # ~140267.55


# Alex's 2017 processed data
bd = utils.get_category_subtypes().reset_index()

bd_desc = bd.description.apply(lambda s: s.lower()).unique()

raw_desc = raw.offence.apply(lambda s: s.lower()).unique()

print(len(raw_desc))
print(len(bd_desc), len(np.intersect1d(bd_desc, raw_desc)),len(np.setdiff1d(bd_desc, raw_desc)))

cd = utils.get_category_subtypes_WIP().reset_index()

cd_desc = cd.description.apply(lambda s: s.lower()).unique()

print(len(raw_desc))
print(len(cd_desc), len(np.intersect1d(cd_desc, raw_desc)),len(np.setdiff1d(cd_desc, raw_desc)))

