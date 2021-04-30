raise DeprecationWarning("no longer working: use analysis/inference.py and/or analysis/periodicity.py")


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
names = pd.read_csv("./data/severity_codes.csv")[["description", "code_original"]]

all_d = pd.read_csv("./daily_adjusted.csv", index_col=["xcor_code", "TimeWindow"])
all_w = pd.read_csv("./weekly_adjusted.csv", index_col=["xcor_code", "DayNumber"])
#all_p = pd.read_csv("./period_adjusted.csv", index_col=["xcor_code", "period"])
all_p = decrypt_csv("./data/weekly-weights.csv.enc", index_col=["xcor_code", "period"])

x = []
for wday in ["M", "Tu", "W", "Th", "F", "Sa", "Su"]:
  for shift in ["n", "d", "e"]:
    x.append("%s-%s" % (wday, shift))

#print(x)

# xsize = 1200
# ysize = 900
# dpi = 200

#plt.tight_layout()

for t in types:

  n = names[names.code_original == t].description.values[0]
  print(t, n)

  d = all_d.loc[t]
  w = all_w.loc[t]
  p = all_p.loc[t]

  count = p["count"].sum()

  # print(d)
  # print(w)
  # print(p)

  p["count_adj2"] = np.reshape(np.outer(w.count_adj / w.count_adj.sum(), d.count_adj / d.count_adj.sum()), 21) * count

  plt.cla()
  plt.bar(x, p["count"], label="observed", alpha=0.5)
  plt.plot(x, p["count_adj"], "o", label="posterior", color="r")
  #plt.plot(x, p["count_adj2"], "o", label="posterior (orthogonal)", color="orange")
  #plt.plot(x, [1/3]*len(x), "o", label="prior", color="k",markersize=2)
  plt.xticks(rotation = 60) # Rotates X-Axis Ticks by 45-degrees
  plt.title("%s (code=%s count=%d)" % (n, t, count))
  plt.xlabel("8h period")
  plt.ylabel("count")
  plt.legend()
  #plt.gcf().set_size_inches(xsize/dpi, ysize/dpi)
  plt.savefig("doc/periodicity-%s.png" % t, bbox_inches="tight")


#plt.show()