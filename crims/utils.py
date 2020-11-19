import numpy as np
import pandas as pd

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


def lad_lookup(lads, subgeog_name):
  lookup = pd.read_csv("./data/gb_geog_lookup.csv.gz", dtype={"OA":str, "LSOA":str, "MSOA":str, "LAD":str, "LAD_NAME":str,
     "LAD_NOMIS": int, "LAD_CM_NOMIS": int, "LAD_CM": str, "LAD_URBAN": str})
  lad_lookup = lookup[lookup.LAD.isin(lads)][[subgeog_name, "LAD"]].drop_duplicates().set_index(subgeog_name, drop=True)
  return lad_lookup


def msoa_from_lsoa(lsoas):
  lookup = pd.read_csv("./data/gb_geog_lookup.csv.gz", dtype={"OA":str, "LSOA":str, "MSOA":str, "LAD":str, "LAD_NAME":str,
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
  """ use lower case with hyphens as per the filenames in the bulk crime data """
  mapping = {
    "Action Fraud": "action-fraud",
    "Avon and Somerset": "avon-and-somerset",
    "Bedfordshire": "bedfordshire",
    "British Transport Police": "british-transport-police",
    "Cambridgeshire": "cambridgeshire",
    "Cheshire": "cheshire",
    "CIFAS": "cifas",
    "Cleveland": "cleveland",
    "Cumbria": "cumbria",
    "Derbyshire": "derbyshire",
    "Devon and Cornwall": "devon-and-cornwall",
    "Dorset": "dorset",
    "Durham": "durham",
    "Dyfed-Powys": "dyfed-powys",
    "Essex": "essex",
    "Financial Fraud Action UK": "financial-fraud-action-uk",
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
    "Metropolitan Police": "metropolitan-police",
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
    "UK Finance": "uk-finance"
  }

  return mapping.get(name, None)

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