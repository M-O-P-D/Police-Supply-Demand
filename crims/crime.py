#crime.py

from zipfile import ZipFile
from pathlib import Path
import requests
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from police_api import PoliceAPI

from .utils import month_range, msoa_from_lsoa, standardise_force_name, standardise_category_name, smooth


class Crime:

  __outcomes_mapping = {
    'Action to be taken by another organisation': False,
    'Awaiting court outcome': True,
    'Court case unable to proceed': True,
    'Court result unavailable': True,
    'Defendant found not guilty': True,
    'Defendant sent to Crown Court': True,
    'Formal action is not in the public interest': False,
    'Further action is not in the public interest': False,
    'Further investigation is not in the public interest': False,
    'Investigation complete; no suspect identified': False,
    'Local resolution': False,
    'Offender deprived of property': True,
    'Offender fined': True,
    'Offender given a caution': True,
    'Offender given a drugs possession warning': True,
    'Offender given absolute discharge': True,
    'Offender given community sentence': True,
    'Offender given conditional discharge': True,
    'Offender given penalty notice': True,
    'Offender given suspended prison sentence': True,
    'Offender ordered to pay compensation': True,
    'Offender otherwise dealt with': True,
    'Offender sent to prison': True,
    'Status update unavailable': False,
    'Suspect charged as part of another case': True,
    'Unable to prosecute suspect': True,
    'Under investigation': False,
    'n/a': False
  }


  # TODO this breaks if not a whole number of years
  """ Class to hold raw crime data and process it as necessary. The dataset is large so loading it is expensive """
  def __init__(self, force_name, start_year, start_month, end_year, end_month):

    # self.year = year
    # self.month = month
    self.original_force_name = force_name
    self.force_name = standardise_force_name(force_name)
    self.api = PoliceAPI()
    self.data = Crime.__get_raw_data(self.force_name, start_year, start_month, end_year, end_month)
    self.data["SuspectDemand"] = self.data["Last outcome category"].apply(lambda c: Crime.__outcomes_mapping[c])
    # assume annual cycle and aggregate years
    self.data["MonthOnly"] = self.data.Month.apply(lambda ym: ym.split("-")[1])


  # returns a GeoDataFrame
  def get_neighbourhoods(self, force_name=None):
    # allow getting neighbourhoods from another force (without having to load all the crime data)
    if force_name is None:
      force_name = self.force_name
    forcepd = self.api.get_force(force_name)

    ns = forcepd.neighbourhoods
    #print(n.locations)# %%

    gdf = gpd.GeoDataFrame({"id": [n.id for n in ns],
                            "name": [n.name for n in ns],
                            "geometry": [Polygon([(p[1], p[0]) for p in n.boundary]) for n in ns]},
                            crs = {"init": "epsg:4326" }).to_crs(epsg=3857)
    return gdf

  # for now just use bulk downloads
  @staticmethod
  def __get_raw_data(force_name, start_year, start_month, end_year, end_month):

    file = "%d-%02d.zip" % (end_year, end_month)

    cache = Path("./data")
    cache.mkdir(parents=True, exist_ok=True) # create if it doesnt already exist

    local_file = cache / file

    if not local_file.is_file():
      print("Data not found locally, downloading...")
      r = requests.get("https://data.police.uk/data/archive/%s" % file)
      open(local_file , 'wb').write(r.content)
      print("...saved to %s" % local_file)

    z = ZipFile(local_file)

    files = ["%s/%s-%s-street.csv" % (d, d, force_name) for d in month_range(start_year, start_month, end_year, end_month)]

    # replace NaNs otherwise data goes missing in groupby operations
    data = pd.concat([pd.read_csv(z.open(f)) for f in files]).fillna("n/a").rename({"Crime type": "crime_type"}, axis=1)
    data.crime_type = data.crime_type.apply(standardise_category_name)

    msoas = msoa_from_lsoa(data["LSOA code"].unique())

    return pd.merge(data, msoas, left_on="LSOA code", right_index=True)

  def get_crime_counts(self):

    # TODO sample annual variability? 3 counts will give *some* indication?

    # count monthly incidence by time, space and type. note this is an *annual* incidence rate
    counts = self.data[["MSOA", "crime_type", "MonthOnly", "Crime ID"]]

    counts = counts.rename({"Crime ID": "count"}, axis=1) \
      .groupby(["MSOA", "MonthOnly", "crime_type"]) \
      .count() \
      .unstack(level=1, fill_value=0)

    # ensure all data accounted for
    assert counts.sum().sum() == len(self.data)

    # counts["count"] = counts["count"].astype(float) * 12 / 3
    counts = counts.astype(float) * 12 / 3

    # smooth counts (ensuring numbers ar conserved)
    before = counts.sum()
    counts = counts.apply(lambda r: smooth(r.values, 7))
    assert np.all(counts.sum() == before)

    # the incidences are the lambdas for sampling arrival times
    return counts

  # likelihood of identifying a suspect per category and geography?
  def get_crime_outcomes(self):

    # get reported crimes
    outcomes = self.data[["MSOA", "crime_type", "SuspectDemand", "Crime ID"]] \
      .rename({"Crime ID": "count"}, axis=1) \
      .groupby(["MSOA", "crime_type", "SuspectDemand"]) \
      .count() \
      .unstack(level=2, fill_value=0) #.reset_index()

    # # ensure all data accounted for
    assert outcomes.sum().sum() == len(self.data)

    outcomes.columns = outcomes.columns.droplevel(0)
    outcomes.rename({False: "NoSuspect", True: "Suspect"}, axis=1, inplace=True)
    #
    outcomes["pSuspect"] = outcomes.Suspect / outcomes.sum(axis=1)

    return outcomes

  def get_category_breakdown(self): # note this is e.g. West Yorkshire not west-yorkshire
    # TODO get original data and process it, see https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/928924/prc-pfa-mar2013-onwards-tables.ods
    # and https://github.com/M-O_P-D/crime_sim_toolkit/blob/master/data_manipulation/MappingCrimeCat2CrimeDes.ipynb
    file = "../crime_sim_toolkit/crime_sim_toolkit/src/prc-pfa-201718_new.csv"

    raw = pd.read_csv(file).rename({"Force_Name": "force",  "Policeuk_Cat": "category", "Offence_Description": "description"}, axis=1)

    #print(raw.force.unique())

    # add antisocial behaviour
    asb = pd.DataFrame(data={"force": raw.force.unique(), "category": "Anti-social behaviour", "description": "Anti-social behaviour", "Number_of_Offences": 1})
    raw = raw.append(asb)

    raw.force = raw.force.apply(standardise_force_name)
    raw.category = raw.category.apply(standardise_category_name)

    cats = raw.groupby(["force", "category", "description"]).sum() \
      .drop(["Unnamed: 0", "Financial_Quarter"], axis=1) \
      .rename({"Number_of_Offences": "offences"}, axis=1)

    cat_totals = cats.groupby(level=[0,1]).sum()

    cats = pd.merge(cats, cat_totals, left_index=True, right_index=True, suffixes=["", "_cat"])
    cats["proportion"] = cats.offences / cats.offences_cat

    return cats.loc[self.force_name]

