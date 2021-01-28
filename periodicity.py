
import pandas as pd
import matplotlib.pyplot as plt

dpi=80
xsize = 320
ysize = 240

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

def dow_map(dow):
  weekdays = ["M","T","W","Th","F","S","Su"]
  return weekdays[dow]

def tod_map(t):
  tod = ["Night", "Day", "Evening"]
  return tod[t]

crimes = pd.read_csv("./data/Playing_Periodicity.csv").drop(["MonthCreated","WeekCreated", "DayCreated"], axis=1)

print(crimes.head())

# expand out counts
total = crimes.TotalCreated.sum()
crimes = crimes.reindex(crimes.index.repeat(crimes.TotalCreated)).drop("TotalCreated", axis=1)
assert len(crimes) == total

# fix codes that have turned into dates
crimes.xcor_code = crimes.xcor_code.apply(fix_code)

# drop subcode detail
crimes.drop(["xcor_code.1", "xcor_lkhocsubcodename"], axis=1, inplace=True)
# adjust day number so that 0 is monday, 6 is sunday
crimes.DayNumber = crimes.DayNumber.apply(lambda d: d-1)
crimes.TimeWindow = crimes.TimeWindow.apply(intraday_enum)

#crimes.set_index(["xcor_code", "xcor_lkhoccodename"], inplace=True)
#crimes.set_index(["YearCreated", "MonthNumber", "DayNumber", "TimeWindow"], inplace=True)

# YearCreated  MonthNumber  DayNumber  TimeWindow xcor_code      xcor_lkhoccodename
crimes = crimes.groupby(["YearCreated", "MonthNumber", "DayNumber", "TimeWindow", "xcor_code", "xcor_lkhoccodename"], as_index=False).size() \
  .rename({"YearCreated": "year", "MonthNumber": "month", "DayNumber": "dow", "TimeWindow": "time", "size": "count"}, axis=1)
# crimes = crimes.groupby(["DayNumber", "TimeWindow", "xcor_code", "xcor_lkhoccodename"], as_index=False).size() \
#   .rename({"DayNumber": "dow", "TimeWindow": "time", "size": "count"}, axis=1)

assert crimes["count"].sum() == total

print(crimes.head())

# Weekly periodicity

weekly = crimes.drop(["year", "month", "time"], axis=1) \
               .groupby(["xcor_code", "xcor_lkhoccodename", "dow"]).sum() \
               .reset_index().set_index(["xcor_code", "xcor_lkhoccodename"])
print(weekly.head())

assert weekly["count"].sum() == total

weekly.to_csv("./data/weekly.csv")

weekly.dow = weekly.dow.apply(dow_map)

totals = weekly.reset_index().groupby(["xcor_code", "xcor_lkhoccodename"]).sum()
totals = totals[totals["count"] > 49]
print(totals.head())

# ngraphs = len(totals)
# print(len(totals))

for i in totals.index:
  print(i[1])
  w = weekly.loc[i]
  plt.cla()
  plt.bar(w.dow, w["count"].values)
  plt.ylabel("Count (2y period)")
  plt.title("%s (%s)" % (i[1], i[0]))
  plt.gcf().set_size_inches(xsize/dpi, ysize/dpi) # not working, get 400x300 not 320x240
  plt.savefig("doc/weekly-%s.png" % i[0].replace("/", "-"))


# Daily periodicity

daily = crimes.drop(["year", "month", "dow"], axis=1) \
               .groupby(["xcor_code", "xcor_lkhoccodename", "time"]).sum() \
               .reset_index().set_index(["xcor_code", "xcor_lkhoccodename"])
print(daily.head())

assert daily["count"].sum() == total

daily.to_csv("./data/daily.csv")

daily.time = daily.time.apply(tod_map)

totals = daily.reset_index().groupby(["xcor_code", "xcor_lkhoccodename"]).sum()
totals = totals[totals["count"] > 49]

print(totals.head())

ngraphs = len(totals)
print(len(totals))

for i in totals.index:
  print(i[1])
  d = daily.loc[i]
  plt.cla()
  plt.bar(d.time, d["count"].values)
  plt.ylabel("Count (2y period)")
  plt.title("%s (%s)" % (i[1], i[0]))
  plt.gcf().set_size_inches(xsize/dpi, ysize/dpi)
  plt.savefig("doc/daily-%s.png" % i[0].replace("/", "-"), dpi=dpi)
  #break

#plt.show()

