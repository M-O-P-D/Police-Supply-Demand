
import pandas as pd
import matplotlib.pyplot as plt

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

crimes = pd.read_csv("./data/Playing_Periodicity.csv").drop(["MonthCreated","WeekCreated", "DayCreated"], axis=1)

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
crimes["period"] = crimes.DayNumber * 3 + crimes.TimeWindow

#crimes.set_index(["xcor_code", "xcor_lkhoccodename"], inplace=True)
#crimes.set_index(["YearCreated", "MonthNumber", "DayNumber", "TimeWindow"], inplace=True)

print(crimes.head())

crimes["count"] = 1

# print(crimes.xcor_code.unique())

weekly = crimes[crimes.YearCreated==2020].drop(["YearCreated", "MonthNumber", "DayNumber", "TimeWindow"], axis=1) \
               .groupby(["xcor_code", "xcor_lkhoccodename", "period"]).sum() \
               .reset_index().set_index(["xcor_code", "xcor_lkhoccodename"])

print(weekly.head())

#assert weekly["count"].sum() == total

weekly.to_csv("./data/weekly.csv")

# w = weekly.loc[("04-1", "Manslaughter")]
# print(w)
# plt.plot(w.period.values/3, w["count"].values, "o")

w = weekly.loc[("105A", "Assault Without Injury")]
print(w)
plt.plot(w.period.values/3, w["count"].values, "o")

plt.show()
