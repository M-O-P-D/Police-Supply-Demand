
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from crims.encryption import encrypt_csv, decrypt_csv

sns.set_theme(style="whitegrid")

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
  "04-Jan": "04-1",
  "04-Apr": "04-4",
  "04-Aug": "04-8",
  "04-Jul": "04-7",
  "04-Oct": "04-8"
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

crimes = decrypt_csv("./data/Playing_Periodicity.csv.enc").drop(["MonthCreated","WeekCreated", "DayCreated"], axis=1)

# fix codes that have turned into dates
crimes.xcor_code = crimes.xcor_code.apply(fix_code)

# create crime description lookup
#codes = crimes.xcor_code.unique()

code_lookup = crimes[["xcor_code", "xcor_lkhoccodename"]].set_index("xcor_code").drop_duplicates()

print(code_lookup.head())
print(len(code_lookup))

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
crime_weights["period"] = crime_weights["DayNumber"] * 3 + crime_weights["TimeWindow"]
crime_weights = crime_weights.drop(["DayNumber", "TimeWindow"], axis=1).set_index(["xcor_code", "period"])
assert crime_weights["count"].sum() == total

totals = crime_weights.reset_index().groupby(["xcor_code"]).sum("count").drop("period", axis=1).rename({"count": "total"}, axis=1)
assert totals["total"].sum() == total

# add missing entries as zeros
idx = [level.unique() for level in crime_weights.index.levels]
crime_weights = crime_weights.reindex(pd.MultiIndex.from_product(idx)).fillna(0)

print(crime_weights.head(25))

# join with totals
crime_weights = crime_weights.join(totals) # set_index("xcor_code").
crime_weights["weight"] = crime_weights["count"] / crime_weights["total"] * 21 # 21 possible periods
print(crime_weights.head(45))
assert crime_weights["count"].sum() == total

#crime_weights.to_csv("data/weekly-weights.csv", index=False)
encrypt_csv(crime_weights, "data/weekly-weights.csv.enc", with_index=False)

if DO_GRAPHS:

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



