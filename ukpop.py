
import pandas as pd
import ukpopulation.snppdata as SNPPData
#import ukpopulation.myedata as MYEData
import ukcensusapi.Nomisweb as CensusApi

def get_census_data(geogs):
  api = CensusApi.Nomisweb("/home/az/.ukcensusapi")

  nomis_lad_codes = api.get_lad_codes(geogs)

  nomis_lsoa_codes = api.get_geo_codes(nomis_lad_codes, CensusApi.Nomisweb.GeoCodeLookup["LSOA11"])

  # categories selected from the metadata
  # "C_AGE": {
  #   "1": "Age 0 to 24",
  #   "2": "Age 25 to 49",
  #   "3": "Age 50 to 64",
  #   "4": "Age 65 and over"
  # },
  # "C_ETHPUK11": {
  #   "1": "White: Total",
  #   "6": "Mixed/multiple ethnic group: Total",
  #   "11": "Asian/Asian British: Total",
  #   "17": "Black/African/Caribbean/Black British: Total",
  #   "21": "Other ethnic group: Total",
  # },  

  table = "LC2101EW"
  table_internal = "NM_801_1"
  query_params = {
    "date": "latest",
    "select": "GEOGRAPHY_CODE,C_SEX,C_AGE,C_ETHPUK11,OBS_VALUE",
    "C_SEX": "1,2",
    "C_AGE": "1,2,3,4",
    "C_ETHPUK11": "1,6,11,17,21",
    "MEASURES": "20100",
    #"geography": "1249912854...1249914188,1249934269...1249934286,1249934384...1249934386,1249934632...1249934632,1249934674...1249934674,1249934696...1249934697,"
    #  "1249934752...1249934764,1249934774...1249934778,1249935219...1249935219,1249935357...1249935365"
  }
  
  query_params["geography"] = nomis_lsoa_codes
  lc2101ew_lsoa = api.get_data(table, query_params)

  query_params["geography"] = nomis_lad_codes
  lc2101ew_lad = api.get_data(table, query_params)

  # ensure geogs are consistent
  assert lc2101ew_lsoa["OBS_VALUE"].sum() == lc2101ew_lad["OBS_VALUE"].sum()

  return lc2101ew_lsoa, lc2101ew_lad


def get_population_data(geogs):
  # mye = MYEData.MYEData()
  # wy_mye2108 = mye.filter(wy, 2018)
  # print(wy_mye2108.head())
  snpp = SNPPData.SNPPData()
  raw = snpp.filter(geogs, 2020).drop("PROJECTED_YEAR_NAME", axis=1)

  # now aggregrate ages into same groups as census data (see above)
  data1 = raw[raw.C_AGE < 25].groupby(["GEOGRAPHY_CODE", "GENDER"]).sum().reset_index()
  data1.C_AGE = 1
  data2 = raw[(raw.C_AGE >= 25) & (raw.C_AGE < 50)].groupby(["GEOGRAPHY_CODE", "GENDER"]).sum().reset_index()
  data2.C_AGE = 2
  data3 = raw[(raw.C_AGE >= 50) & (raw.C_AGE < 65)].groupby(["GEOGRAPHY_CODE", "GENDER"]).sum().reset_index()
  data3.C_AGE = 3
  data4 = raw[raw.C_AGE >= 65].groupby(["GEOGRAPHY_CODE", "GENDER"]).sum().reset_index()
  data4.C_AGE = 4
  
  #"GEOGRAPHY_CODE", "GENDER", "C_AGE", "OBS_VALUE"
  return pd.concat([data1, data2, data3, data4])

#      Bradford     Calderdale   Kirklees     Leeds        Wakefield
wy = ["E08000032", "E08000033", "E08000034", "E08000035", "E08000036"]

wy_snpp2020 = get_population_data(wy)
print("2020 populations")
print(wy_snpp2020.groupby(["GEOGRAPHY_CODE"]).sum().OBS_VALUE)

wy_lsoa, wy_lad = get_census_data(wy)
print(wy_lsoa.head())
print(wy_lad.head())


