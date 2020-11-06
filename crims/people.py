import numpy as np
import pandas as pd
import ukpopulation.snppdata as SNPPData
#import ukpopulation.myedata as MYEData
import ukcensusapi.Nomisweb as CensusApi

from .utils import lad_lookup

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

# from nismod/microsimulation
# def unlistify(table, columns, values):
#   """
#   Converts an n-column table of counts into an n-dimensional array of counts
#   """

#   sizes = [len(table[c].unique()) for c in columns]

#   pivot = table.pivot_table(index=columns, values=values)
#   # order must be same as column order above
#   array = np.zeros(sizes, dtype=int)
#   array[tuple(pivot.index.codes)] = pivot.values.flat

#   assert np.sum(array) == table[values].sum()
#   return array

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
  # mye2108 = mye.filter(geogs, 2018)
  # print(mye2108.head())
  snpp = SNPPData.SNPPData()
  snpp_syoa = snpp.filter(geogs, 2020).drop("PROJECTED_YEAR_NAME", axis=1)

  # got from single year of age to groups
  return map_ages(snpp_syoa)

def get_scaled_population(geogs):

  # SNPP is per LAD so need different scalings for MSOAs in different LADs
  msoa_lad_lookup = lad_lookup(geogs, "MSOA")
  print("MSOAs: %d" % len(msoa_lad_lookup))

  # get SNPPs
  snpp = get_population_data(geogs)
  snpp.rename({"GEOGRAPHY_CODE": "LAD", "GENDER": "C_SEX"}, axis=1, inplace=True)
  snpp.set_index(["LAD", "C_SEX", "C_AGE"], inplace=True, drop=True)
  # print("2020 populations")
  # print(snpp.groupby(level=[0]).sum())

  # get census data at MSOA and LAD scales (latter for computing scaling factors)
  census_msoa, census_lad = get_census_data(geogs)
  census_msoa.rename({"GEOGRAPHY_CODE": "MSOA"}, axis=1, inplace=True)
  census_lad.rename({"GEOGRAPHY_CODE": "LAD"}, axis=1, inplace=True)
  census_msoa = pd.merge(census_msoa, msoa_lad_lookup, left_on="MSOA", right_index=True).set_index(["LAD", "MSOA", "C_SEX", "C_AGE", "C_ETHPUK11"])

  # drop ethnicity from LAD level data (we have no ethnicity data in SNPP)
  census_lad = census_lad.groupby(["LAD", "C_SEX", "C_AGE"]).sum().drop("C_ETHPUK11", axis=1)
  snpp.rename({"OBS_VALUE": "PROJ_VALUE"}, axis=1, inplace=True)

  # compute a scaling factor for population by LAD, gender and age
  lad_sex_age_factors = pd.merge(census_lad, snpp, left_index=True, right_index=True)
  lad_sex_age_factors["SCALING"] = lad_sex_age_factors.PROJ_VALUE / lad_sex_age_factors.OBS_VALUE

  # merge the scaling factor into the population data and compute projected counts
  census_msoa = pd.merge(census_msoa, lad_sex_age_factors[["SCALING"]], left_index=True, right_index=True)
  census_msoa["SCALING"] *= census_msoa["OBS_VALUE"]
  census_msoa.rename({"SCALING": "PROJ_VALUE"}, axis=1, inplace=True)

  return census_msoa

