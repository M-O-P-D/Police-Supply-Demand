import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from crims.encryption import decrypt_csv

# 1 = 8 counts
# 10A = 32
# 17B = 137
# 22B = 544
# 30C = 2103
# 8R = 7996
# 105A = 16083

types = ["1", "10A", "17B", "22B", "30C", "8R", "105A"] #[1, 100]

all_d = pd.read_csv("./daily_adjusted.csv", index_col=["xcor_code", "TimeWindow"])
all_w = pd.read_csv("./weekly_adjusted.csv", index_col=["xcor_code", "DayNumber"])
all_p = pd.read_csv("./period_adjusted.csv", index_col=["xcor_code", "period"])


for t in types:

  d = all_d.loc[t]
  w = all_w.loc[t]
  p = all_p.loc[t]

  count = p["count"].sum()

  # print(d)
  # print(w)
  # print(p)

  p["count_p2"] = np.reshape(np.outer(w.count_p / w.count_p.sum(), d.count_p / d.count_p.sum()), 21) * count

  plt.cla()
  plt.bar(p.index, p["count"], label="actual")
  plt.plot(p.index, p["count_p"], "o", label="posterior", color="r")
  plt.plot(p.index, p["count_p2"], "o", label="orthogonal", color="k")
  plt.title("%s (count=%d)" % (t, count))
  plt.xlabel("8h period")
  plt.xlabel("count")
  plt.legend()
  plt.savefig("doc/periodicity-%s.png" % t, dpi=200)


#plt.show()