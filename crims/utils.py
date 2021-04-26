import os
import numpy as np
import pandas as pd
from pathlib import Path

from .encryption import decrypt_csv

# this needs to be overridden if run from a directory other than the project root
DEFAULT_DATA_PATH="./data"

def get_data_path(filename=""):
  return Path(os.getenv("CRIMS_DATA_PATH", DEFAULT_DATA_PATH)) / filename

# inclusive range of months
def month_range(start_year, start_month, end_year, end_month):

  assert start_year <= end_year
  if start_year == end_year:
    assert start_month <= end_month

  d = []
  while True:
    d.append("%4d-%02d" % (start_year, start_month))
    start_month += 1
    if start_month == 13:
      start_year += 1
      start_month = 1
    if start_year > end_year or (start_year == end_year and start_month > end_month):
      break
  return d

# decorator for creating static function variables
def static_vars(**kwargs):
  def decorate(func):
    for k in kwargs:
      setattr(func, k, kwargs[k])
    return func
  return decorate

@static_vars(weekly_weights=decrypt_csv(get_data_path("weekly-weights.csv.enc")))
def get_periodicity(dow_adj, days_in_month, category):

  cycle = get_periodicity.weekly_weights[get_periodicity.weekly_weights.xcor_code==category][["period", "weight"]]

  # if no data assume no daily/weekly periodicity
  if cycle.empty:
    return np.ones(3 * days_in_month)

  # align and repeat week to the current month. NB Mo=0, Su=6
  weights = np.tile(np.roll(cycle.weight, -3*dow_adj), 5)[:3*days_in_month]

  # renormalise to mean weight of 1 - this is a scaling factor applied to the monthly intensity
  weights *= len(weights) / weights.sum()

  return weights


def lad_lookup(lads, subgeog_name):
  lookup = pd.read_csv(get_data_path("gb_geog_lookup.csv.gz"), dtype={"OA":str, "LSOA":str, "MSOA":str, "LAD":str, "LAD_NAME":str,
     "LAD_NOMIS": int, "LAD_CM_NOMIS": int, "LAD_CM": str, "LAD_URBAN": str})
  lad_lookup = lookup[lookup.LAD.isin(lads)][[subgeog_name, "LAD"]].drop_duplicates().set_index(subgeog_name, drop=True)
  return lad_lookup


def msoa_from_lsoa(lsoas):
  lookup = pd.read_csv(get_data_path("gb_geog_lookup.csv.gz"), dtype={"OA":str, "LSOA":str, "MSOA":str, "LAD":str, "LAD_NAME":str,
     "LAD_NOMIS": int, "LAD_CM_NOMIS": int, "LAD_CM": str, "LAD_URBAN": str})
  msoa_lookup = lookup[lookup.LSOA.isin(lsoas)][["LSOA", "MSOA"]].drop_duplicates().set_index("LSOA", drop=True)
  return msoa_lookup

def _pascal_weights(n):
  if n == 1:
    return np.array([1.0])
  wm = _pascal_weights(n-1)
  w = np.append([0], wm) + np.append(wm, [0])
  return w / sum(w)


def smooth(a, n):
  # odd n only to avoid lagging
  assert n % 2 == 1
  w = _pascal_weights(n)
  m = n//2
  s = a * w[m]
  for i in range(1,m+1):
    s += w[m-i] * np.roll(a, -i) + w[m+i] * np.roll(a,i)
  return s


def standardise_force_name(name):
  """use lower case with hyphens as per the filenames in the bulk crime data"""
  mapping = {
    "Avon & Somerset": "avon-and-somerset",
    "Avon and Somerset": "avon-and-somerset",
    "Bedfordshire": "bedfordshire",
    "Cambridgeshire": "cambridgeshire",
    "Cheshire": "cheshire",
    "Cleveland": "cleveland",
    "Cumbria": "cumbria",
    "Derbyshire": "derbyshire",
    "Devon & Cornwall": "devon-and-cornwall",
    "Devon and Cornwall": "devon-and-cornwall",
    "Dorset": "dorset",
    "Durham": "durham",
    "Dyfed-Powys": "dyfed-powys",
    "Essex": "essex",
    "Gloucestershire": "gloucestershire",
    "Greater Manchester": "greater-manchester",
    "Gwent": "gwent",
    "Hampshire": "hampshire",
    "Hertfordshire": "hertfordshire",
    "Humberside": "humberside",
    "Kent": "kent",
    "Lancashire": "lancashire",
    "Leicestershire": "leicestershire",
    "Lincolnshire": "lincolnshire",
    "London, City of": "city-of-london",
    "City of London": "city-of-london",
    "Merseyside": "merseyside",
    "Metropolitan Police": "metropolitan",
    "Norfolk": "norfolk",
    "North Wales": "north-wales",
    "North Yorkshire": "north-yorkshire",
    "Northamptonshire": "northamptonshire",
    "Northumbria": "northumbria",
    "Nottinghamshire": "nottinghamshire",
    "South Wales": "south-wales",
    "South Yorkshire": "south-yorkshire",
    "Staffordshire": "staffordshire",
    "Suffolk": "suffolk",
    "Surrey": "surrey",
    "Sussex": "sussex",
    "Thames Valley": "thames-valley",
    "Warwickshire": "warwickshire",
    "West Mercia": "west-mercia",
    "West Midlands": "west-midlands",
    "West Yorkshire": "west-yorkshire",
    "Wiltshire": "wiltshire",
  }

  # just return the input if is a value in the map (i.e. already standardised)
  if name in mapping.values(): return name

  return mapping[name]
  #return mapping.get(name)

def standardise_category_name(typestr):
  return typestr.lower()
#   'Anti-social behaviour', 'Bicycle theft', 'Burglary',
#   'Criminal damage and arson', 'Drugs', 'Other crime', 'Other theft',
#        'Possession of weapons', 'Public order', 'Robbery', 'Shoplifting',
#        'Theft from the person', 'Vehicle crime',
#        'Violence and sexual offences'],
# Index(['Bicycle Theft', 'Burglary', 'Criminal Damage and Arson', 'Drugs',
#        'Other Theft', 'Other crime', 'Possession of Weapons', 'Public Order',
#        'Robbery', 'Shoplifting', 'Theft from the Person', 'Vehicle Crime',
#        'Violence and Sexual Offences'],
#       dtype='object', name='category')


def map_code(original_code):

  # TODO (low importance) seems like corporate manslaughter "4.10" is being truncated to 4.1 (manslaughter)
  mapping = {
    "30A": "30C",
    "28A": "28C",
    "4.1": "1, 4.1/2/10",
    "4.2": "1, 4.1/2/10",
    "1": "1, 4.1/2/10",
    "1/4.1/4.10/4.2": "1, 4.1/2/10"
  }

  return mapping.get(original_code, original_code)

# Using the lastest ONS data, when it works
def get_category_subtypes():

  cached_data = get_data_path("detailed-offence-counts.csv")

  if not cached_data.is_file():
    raw = pd.read_excel("https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/928924/prc-pfa-mar2013-onwards-tables.ods", sheet_name="2019-20")
    raw.to_csv(cached_data, index=False)
  else:
    raw = pd.read_csv(cached_data)

  # remove extraneous and rename for consistency
  non_geographic = ['Action Fraud', 'British Transport Police', 'CIFAS', 'UK Finance']
  raw = raw[~raw["Force Name"].isin(non_geographic)].drop(["Financial Year", "Financial Quarter", "Offence Subgroup"], axis=1) \
    .rename({"Force Name": "force", "Offence Group": "category", "Offence Description": "description", "Offence Code": "code_original", "Offence Count": "count"}, axis=1)

  # duplicate code column and modify values that don't match the codes in the severity scores
  raw["code_severity"] = raw.code_original.apply(map_code)

  raw.category = raw.category.apply(standardise_category_name)
  raw.force = raw.force.apply(standardise_force_name)

  # manual match of police.uk to ONS crime descriptions -> codes
  cat_mapping = pd.read_csv(get_data_path("policeuk-ons-code-join.csv"))[["POLICE_UK_CAT_MAP_category", "ONS_COUNTS_code", "ONS_SEVERITY_weight"]]
  cat_mapping.POLICE_UK_CAT_MAP_category = cat_mapping.POLICE_UK_CAT_MAP_category.apply(standardise_category_name)

  #print(cat_mapping.head())

  #raw["POLICE_UK_CAT_MAP_category"] = raw.code_original.apply()

  cats = raw.groupby(["force", "category", "description", "code_original"]).sum().reset_index()

  cats = pd.merge(cats, cat_mapping, how="left", left_on="code_original", right_on="ONS_COUNTS_code").set_index(["force", "POLICE_UK_CAT_MAP_category"]).drop(["category", "ONS_COUNTS_code"], axis=1)

  # now append antisocial behaviour
  asb = pd.DataFrame({"force": raw.force.unique(),
                      "POLICE_UK_CAT_MAP_category": "anti-social behaviour",
                      "description": "Anti-social behaviour",
                      "code_original": "(asb)",
                      "ONS_SEVERITY_weight": 1.0,
                      "count": 1}) \
    .set_index(["force", "POLICE_UK_CAT_MAP_category"])
  cats = cats.append(asb)

  # turn counts into per-category proportions
  cat_totals = cats[["count"]].groupby(level=[0,1]).sum()
  cats = pd.merge(cats, cat_totals, left_index=True, right_index=True, suffixes=["", "_total"])
  cats["proportion"] = cats["count"] / cats.count_total

  return cats.drop(["count", "count_total"], axis=1)

# # Using Alex's original data
# def get_category_subtypes():
#   # TODO get original data and process it, see https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/928924/prc-pfa-mar2013-onwards-tables.ods
#   # and https://github.com/M-O_P-D/crime_sim_toolkit/blob/master/data_manipulation/MappingCrimeCat2CrimeDes.ipynb
#   file = "./data/prc-pfa-201718_new.csv"

#   raw = pd.read_csv(file).rename({"Force_Name": "force",  "Policeuk_Cat": "category", "Offence_Description": "description"}, axis=1)

#   non_geographic = ['Action Fraud', 'British Transport Police', 'CIFAS', 'Financial Fraud Action UK', 'UK Finance']
#   raw = raw[~raw["force"].isin(non_geographic)]
#   #print(raw.force.unique())

#   # add antisocial behaviour
#   asb = pd.DataFrame(data={"force": raw.force.unique(), "category": "Anti-social behaviour", "description": "Anti-social behaviour", "Number_of_Offences": 1})
#   raw = raw.append(asb)

#   raw.force = raw.force.apply(standardise_force_name)
#   raw.category = raw.category.apply(standardise_category_name)

#   cats = raw.groupby(["force", "category", "description"]).sum() \
#     .drop(["Unnamed: 0", "Financial_Quarter"], axis=1) \
#     .rename({"Number_of_Offences": "offences"}, axis=1)

#   cat_totals = cats.groupby(level=[0,1]).sum()

#   cats = pd.merge(cats, cat_totals, left_index=True, right_index=True, suffixes=["", "_cat"])
#   cats["proportion"] = cats.offences / cats.offences_cat

#   return cats
