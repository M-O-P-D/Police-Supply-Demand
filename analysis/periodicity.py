import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from crims.encryption import encrypt_csv, decrypt_csv
from crims.utils import get_category_subtypes

from crims.crime import Crime

#sns.set_theme(style="whitegrid")

DO_GRAPHS = False

dpi = 100
xsize = 640
ysize = 480

intraday_mapping = {
  "Daytime": 1,
  "Evening": 2,
  "Overnight": 0
}

code_adjustments = {
  "04-Jan": "4.1",
  "04-Apr": "4.4",
  "04-Aug": "4.8",
  "04-Jul": "4.7",
  "04-Oct": "4.10", # TODO this ends up as 4.1 when save to csv
  "37/2": "37.2"
}

def intraday_enum(t):
  return intraday_mapping[t]

def fix_code(c):
  # adjust or return input
  return code_adjustments.get(c, c)

weekdays = ["M","Tu","W","Th","F","Sa","Su"]
def dow_map(dow):
  return weekdays[dow]

tod = ["Night", "Day", "Evening"]
def tod_map(t):
  return tod[t]

# this is 2y of data, 1/2019-12/2020 time given as year, month, day of week, time of day (but not day of month)
crimes = decrypt_csv("./data/Playing_Periodicity.csv.enc").drop(["MonthCreated","WeekCreated", "DayCreated"], axis=1)

# # fix codes that have turned into dates or are otherwise mismatched
crimes.xcor_code = crimes.xcor_code.apply(fix_code)

# remove unwanted codes for "skeleton crime" and fraud
crimes = crimes[~crimes.xcor_code.isin(["5550", "NFIB1"])]

print(crimes[crimes.xcor_code == "4.10"])
# create crime description lookup
#codes = crimes.xcor_code.unique()

code_lookup = crimes[["xcor_code", "xcor_lkhoccodename"]].set_index("xcor_code").drop_duplicates()

# print(code_lookup.head())
# print(len(code_lookup))

# drop descriptions and expand out counts
total = crimes.TotalCreated.sum()
crimes = crimes.drop(["xcor_lkhoccodename", "xcor_code.1", "xcor_lkhocsubcodename"], axis=1) \
  .reindex(crimes.index.repeat(crimes.TotalCreated)).drop("TotalCreated", axis=1)
assert len(crimes) == total

# adjust day number so that 0 is monday, 6 is sunday
crimes.DayNumber = crimes.DayNumber.apply(lambda d: d-1)
crimes.TimeWindow = crimes.TimeWindow.apply(intraday_enum)

# get counts by day and time of day

crime_weights = crimes.groupby(["DayNumber", "TimeWindow", "xcor_code"], as_index=False).size() \
  .rename({"size": "count"}, axis=1)

crime_weights_w = crimes.groupby(["DayNumber", "xcor_code"], as_index=False).size() \
  .rename({"size": "count"}, axis=1).set_index(["xcor_code", "DayNumber"])
crime_weights_d = crimes.groupby(["TimeWindow", "xcor_code"], as_index=False).size() \
  .rename({"size": "count"}, axis=1).set_index(["xcor_code", "TimeWindow"])

crime_weights["period"] = crime_weights["DayNumber"] * 3 + crime_weights["TimeWindow"]
crime_weights = crime_weights.drop(["DayNumber", "TimeWindow"], axis=1).set_index(["xcor_code", "period"])
assert crime_weights_w["count"].sum() == total
assert crime_weights_d["count"].sum() == total
assert crime_weights["count"].sum() == total

# apply Bayesian inference to 21 x 8 hour cycle
crime_weights = crime_weights.unstack(level=1, fill_value=0.0)

totals = crime_weights.sum(axis=1).rename("total")

# weight prior so that total (obs+prior) is at least 1 per week
# alpha = np.full(max(104-r.sum(), 1), 21)
crime_weights_s = crime_weights.T.apply(lambda r: stats.dirichlet.mean((r + np.full(21, max(104.0-np.sum(r), 1.0)))) * np.sum(r)).T
assert np.allclose(totals.values, crime_weights_s.sum(axis=1).values)

crime_weights_s = crime_weights_s.stack()
crime_weights_s = crime_weights_s.join(crime_weights.stack(), lsuffix="_adj")
crime_weights_s = crime_weights_s.join(totals)

#crime_weights_s["weight"] = crime_weights_s["count_p"] / crime_weights_s["total"] * 21 # 21 possible periods
print(crime_weights_s.head(45))
#assert crime_weights["count"].sum() == total
#crime_weights_s.to_csv("./period_adjusted.csv")


# ######################################################
# # apply Bayesian inference to shift cycle aggregated across week
# print(crime_weights_d)
# crime_weights_d = crime_weights_d.unstack(level=1, fill_value=0.0)
# print(crime_weights_d)

# alpha = np.full(3, 1/3) # 1 per day prior
# crime_weights_ds = crime_weights_d.T.apply(lambda r: stats.dirichlet.mean((r + alpha)) * np.sum(r)).T
# assert np.allclose(totals.values, crime_weights_d.sum(axis=1).values)

# crime_weights_ds = crime_weights_ds.stack()
# crime_weights_ds = crime_weights_ds.join(crime_weights_d.stack(), lsuffix="_adj")

# print(crime_weights_ds.head(25))
# assert crime_weights_ds.sum()["count_adj"] == crime_weights_ds.sum()["count"]
# crime_weights_ds.to_csv("./daily_adjusted.csv")

# ######################################################
# # apply Bayesian inference to daily cycle aggregated across shift
# print(crime_weights_w)
# crime_weights_w = crime_weights_w.unstack(level=1, fill_value=0.0)
# print(crime_weights_w)

# alpha = np.full(7, 1) # 1 per day prior
# crime_weights_ws = crime_weights_w.T.apply(lambda r: stats.dirichlet.mean((r + alpha)) * np.sum(r)).T
# assert np.allclose(totals.values, crime_weights_w.sum(axis=1).values)

# crime_weights_ws = crime_weights_ws.stack()
# crime_weights_ws = crime_weights_ws.join(crime_weights_w.stack(), lsuffix="_adj")

# print(crime_weights_ws.head(25))
# assert crime_weights_ws.sum()["count_adj"] == crime_weights_ws.sum()["count"]
# crime_weights_ws.to_csv("./weekly_adjusted.csv")


#crime_weights.to_csv("data/weekly-weights.csv")
encrypt_csv(crime_weights_s, "data/weekly-weights.csv.enc")

# check monthly aggregations have some consistency

crime = Crime("Durham", 2017, 12, 2020, 11)
crime_categories = crime.get_category_breakdown()

# check cats match up
my_cats = crimes.xcor_code.unique()
their_cats = crime_categories["code_original"].unique()

print("codes in local but not in severity lookup:", np.setdiff1d(my_cats, their_cats))
print("codes in severity lookup but not in local data:", np.setdiff1d(their_cats, my_cats))

crime_categories = crime_categories.reset_index()[["code_original", "description", "POLICE_UK_CAT_MAP_category"]]

if DO_GRAPHS:

  crimes_annual = crimes.merge(crime_categories, left_on="xcor_code", right_on="code_original") \
                        .drop(["DayNumber", "TimeWindow", "code_original", "description"], axis=1) \
                        .groupby(["YearCreated", "xcor_code", "POLICE_UK_CAT_MAP_category"], as_index=False).count() \
                        .set_index(["YearCreated", "POLICE_UK_CAT_MAP_category", "xcor_code"]) \
                        .unstack(0, 0)
  crimes_annual.columns = crimes_annual.columns.droplevel()
  print(crimes_annual)

  for i in crimes_annual.index.levels[0].unique():
    print(i)
    crimes_annual.loc[[i]].plot.bar(title=i, ylabel="crimes reported")
    #plt.gcf().set_size_inches(xsize/dpi, ysize/dpi)
    plt.savefig("doc/annual-%s.png" % i.replace(" ", "_"), bbox_inches="tight")
    plt.close()

  crimes_monthly = crimes.merge(crime_categories, left_on="xcor_code", right_on="code_original") \
                        .drop(["DayNumber", "TimeWindow", "code_original", "description"], axis=1) \
                        .groupby(["MonthNumber", "xcor_code", "POLICE_UK_CAT_MAP_category"], as_index=False).count() \
                        .set_index(["MonthNumber", "POLICE_UK_CAT_MAP_category", "xcor_code"]) \
                        .unstack(0, 0)
  crimes_monthly.columns = crimes_monthly.columns.droplevel()
  print(crimes_monthly)
  # assert crimes_monthly.sum().values.sum() == total
  plt.rcParams["figure.figsize"] = [10, 5]
  for i in crimes_monthly.index.levels[0].unique():
    print(i)
    #print(crimes_monthly.loc[[i]].droplevel(0))
    ax = crimes_monthly.loc[[i]].droplevel(0).T.plot.bar(title=i, ylabel="crimes reported", stacked=True)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    #plt.gcf().set_size_inches(xsize/dpi, ysize/dpi)
    plt.savefig("doc/monthly-%s.png" % i.replace(" ", "_"), bbox_inches="tight")
    plt.close()

  # YearCreated  MonthNumber  DayNumber  TimeWindow xcor_code      xcor_lkhoccodename
  crimes = crimes.groupby(["YearCreated", "MonthNumber", "DayNumber", "TimeWindow", "xcor_code"], as_index=False).size() \
    .rename({"YearCreated": "year", "MonthNumber": "month", "DayNumber": "dow", "TimeWindow": "time", "size": "count"}, axis=1)
  crimes.dow = crimes.dow.apply(dow_map)
  crimes.time = crimes.time.apply(tod_map)

  assert crimes["count"].sum() == total

  print(crimes.head())

  # Weekly periodicity (aggregrating intraday), with empties
  weekly = crimes.drop("time", axis=1).groupby(["xcor_code", "dow", "year", "month"]).sum()
  idx = [level.unique() for level in weekly.index.levels]
  weekly = weekly.reindex(pd.MultiIndex.from_product(idx)).fillna(0) \
                .reset_index().set_index(["xcor_code", "dow"]) \
                .drop(["year", "month"], axis=1)
  print(weekly.head(20))
  print(len(weekly))

  # insert zeros where no counts
  assert weekly["count"].sum() == total

  #weekly.to_csv("./data/weekly.csv")

  totals = weekly.reset_index().groupby(["xcor_code"]).sum("count")
  totals = totals[totals["count"] > 49]
  print(totals.head())

  for i in totals.index:
    desc = code_lookup.loc[i, "xcor_lkhoccodename"]
    print(i, desc)
    w = weekly.loc[i].reset_index()
    plt.cla()
    ax = sns.boxplot(x="dow", y="count", data=w, order=weekdays, showfliers = False)#, boxprops=dict(alpha=.3))
    for patch in ax.artists:
      r, g, b, a = patch.get_facecolor()
      patch.set_facecolor((r, g, b, .3))
    sns.stripplot(x="dow", y="count", data=w, order=weekdays)
    #plt.bar(w.dow, w["count"].values)
    plt.ylabel("Weekly frequency")
    plt.ylim(0)
    plt.title("%s (%s)" % (desc, i))
    plt.gcf().set_size_inches(xsize/dpi, ysize/dpi)
    plt.savefig("doc/weekly-%s.png" % i.replace("/", "-"), dpi=dpi)


  # Daily periodicity (aggregrating weekday), with empties
  daily = crimes.drop("dow", axis=1).groupby(["xcor_code", "time", "year", "month"]).sum()
  idx = [level.unique() for level in daily.index.levels]
  daily = daily.reindex(pd.MultiIndex.from_product(idx)).fillna(0) \
              .reset_index().set_index(["xcor_code", "time"]) \
              .drop(["year", "month"], axis=1)
  print(daily.head(20))
  print(len(daily))

  assert daily["count"].sum() == total

  #daily.to_csv("./data/daily.csv")

  totals = daily.reset_index().groupby(["xcor_code"]).sum("count")
  totals = totals[totals["count"] > 49]
  print(totals.head())

  for i in totals.index:
    desc = code_lookup.loc[i, "xcor_lkhoccodename"]
    print(i, desc)
    w = daily.loc[i].reset_index()
    plt.cla()
    ax = sns.boxplot(x="time", y="count", data=w, order=tod, showfliers = False)
    for patch in ax.artists:
      r, g, b, a = patch.get_facecolor()
      patch.set_facecolor((r, g, b, .3))
    sns.stripplot(x="time", y="count", data=w, order=tod)
    plt.ylabel("Daily frequency")
    plt.ylim(0)
    plt.title("%s (%s)" % (desc, i))
    plt.gcf().set_size_inches(xsize/dpi, ysize/dpi)
    plt.savefig("doc/daily-%s.png" % i.replace("/", "-"), dpi=dpi)



