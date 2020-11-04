import numpy as np
import pandas as pd
import ukpopulation.snppdata as SNPPData
#import ukpopulation.myedata as MYEData
import ukcensusapi.Nomisweb as CensusApi

import humanleague as hl

def map_ages(df_syoa):
  # age mapping
  age_mapping = {
    1: (0, 4),
    2: (5, 7),
    3: (8, 9),
    4: (10, 14),
    5: (15, 15),
    6: (16, 17),
    7: (18, 19),
    8: (20, 24),
    9: (25, 29),
    10: (30, 34),
    11: (35, 39),
    12: (40, 44),
    13: (45, 49),
    14: (50, 54),
    15: (55, 59),
    16: (60, 64),
    17: (65, 69),
    18: (70, 74),
    19: (75, 79),
    20: (80, 84),
    21: (85, 99)
  }

  df = pd.DataFrame()

  for k in age_mapping:
    data = df_syoa[(df_syoa.C_AGE >= age_mapping[k][0]) & (df_syoa.C_AGE <= age_mapping[k][1])].groupby(["GEOGRAPHY_CODE", "GENDER"]).sum().reset_index()
    data.C_AGE = k
    df = df.append(data)

  # ensure everyone is accounted for
  assert df_syoa.OBS_VALUE.sum() == df.OBS_VALUE.sum()

  return df.reset_index(drop=True)

def unlistify(table, columns, values):
  """
  Converts an n-column table of counts into an n-dimensional array of counts
  """

  sizes = [len(table[c].unique()) for c in columns]

  print(sizes)

  pivot = table.pivot_table(index=columns, values=values)
  # order must be same as column order above
  array = np.zeros(sizes, dtype=int)
  array[tuple(pivot.index.codes)] = pivot.values.flat

  assert np.sum(array) == table[values].sum()
  return array

def get_census_data(geogs):
  api = CensusApi.Nomisweb("~/.ukcensusapi")

  nomis_lad_codes = api.get_lad_codes(geogs)

  nomis_msoa_codes = api.get_geo_codes(nomis_lad_codes, CensusApi.Nomisweb.GeoCodeLookup["MSOA11"])

  # "C_ETHPUK11": {
  #   "1": "White: Total",
  #   "6": "Mixed/multiple ethnic group: Total",
  #   "11": "Asian/Asian British: Total",
  #   "17": "Black/African/Caribbean/Black British: Total",
  #   "21": "Other ethnic group: Total",
  # },  

  table = "DC2101EW"
  table_internal = "NM_651_1"
  query_params = {
    "date": "latest",
    "select": "GEOGRAPHY_CODE,C_SEX,C_AGE,C_ETHPUK11,OBS_VALUE",
    "C_SEX": "1,2",
    "C_AGE": "1...21",
    "C_ETHPUK11": "1,6,11,17,21",
    "MEASURES": "20100",
  }
  
  query_params["geography"] = nomis_msoa_codes
  dc2101ew_msoa = api.get_data(table, query_params)

  query_params["geography"] = nomis_lad_codes
  dc2101ew_lad = api.get_data(table, query_params)

  # ensure geogs are consistent
  assert dc2101ew_msoa["OBS_VALUE"].sum() == dc2101ew_lad["OBS_VALUE"].sum()

  return dc2101ew_msoa, dc2101ew_lad


def get_population_data(geogs):
  # mye = MYEData.MYEData()
  # wy_mye2108 = mye.filter(wy, 2018)
  # print(wy_mye2108.head())
  snpp = SNPPData.SNPPData()
  snpp_syoa = snpp.filter(geogs, 2020).drop("PROJECTED_YEAR_NAME", axis=1)

  # got from single year of age to groups
  return map_ages(snpp_syoa)


  # # now aggregrate ages into same groups as census data (see above)
  # data1 = raw[raw.C_AGE < 25].groupby(["GEOGRAPHY_CODE", "GENDER"]).sum().reset_index()
  # data1.C_AGE = 1
  # data2 = raw[(raw.C_AGE >= 25) & (raw.C_AGE < 50)].groupby(["GEOGRAPHY_CODE", "GENDER"]).sum().reset_index()
  # data2.C_AGE = 2
  # data3 = raw[(raw.C_AGE >= 50) & (raw.C_AGE < 65)].groupby(["GEOGRAPHY_CODE", "GENDER"]).sum().reset_index()
  # data3.C_AGE = 3
  # data4 = raw[raw.C_AGE >= 65].groupby(["GEOGRAPHY_CODE", "GENDER"]).sum().reset_index()
  # data4.C_AGE = 4
  
  # #"GEOGRAPHY_CODE", "GENDER", "C_AGE", "OBS_VALUE"
  # return pd.concat([data1, data2, data3, data4])

#      Bradford     Calderdale   Kirklees     Leeds        Wakefield
wy = ["E08000032", "E08000033", "E08000034", "E08000035", "E08000036"]

wy_snpp2020 = get_population_data(wy)
print("2020 populations")
print(wy_snpp2020.groupby(["GEOGRAPHY_CODE"]).sum().OBS_VALUE)

wy_msoa, wy_lad = get_census_data(wy)
print(wy_msoa.head())
print(wy_lad.head())
print(wy_snpp2020.head())

lad_age_sex_eth_census = unlistify(wy_lad, ["GEOGRAPHY_CODE", "C_SEX", "C_AGE", "C_ETHPUK11"], "OBS_VALUE")
lad_age_sex_census = np.sum(lad_age_sex_eth_census, axis=3)
lad_age_sex_snpp = unlistify(wy_snpp2020, ["GEOGRAPHY_CODE", "GENDER", "C_AGE"], "OBS_VALUE")

# compute a scaling factor for population by LAD, gender and age
lad_age_sex_scaling = np.divide(lad_age_sex_snpp, lad_age_sex_census)

# now scale up the census populations
lad_age_sex_eth_snpp2020 = lad_age_sex_eth_census.astype(float)
for i in range(5): # no. of eth cats
  lad_age_sex_eth_snpp2020[:,:,:,i] = np.multiply(lad_age_sex_eth_snpp2020[:,:,:,i], lad_age_sex_scaling)


print(lad_age_sex_eth_snpp2020)
print(np.sum(lad_age_sex_eth_census), np.sum(lad_age_sex_eth_snpp2020))


print(len(wy_msoa.GEOGRAPHY_CODE.unique()))
