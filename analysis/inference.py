
import numpy as np
import pandas as pd
from scipy import stats

import matplotlib.pyplot as plt

from crims.encryption import decrypt_csv

dow = ["M", "Tu", "W", "Th", "F", "Sa", "Su"]
tod = ["n", "d", "e"]
x = ["%s-%s" % (dow[x//3], tod[x%3]) for x in range(21)]

# manual calculations equivalent to scipy.dirichlet.mean/var
def mean(c, alpha):
  return (c + alpha) / (np.sum(c) + np.sum(alpha))

def var(c, alpha):
  s = np.sum(c + alpha)
  a = (c + alpha) / s
  return a * (1 - a) / (s + 1)

def posterior(w, obs):

  count = obs.sum()
  alpha = np.full(len(obs), YEARS_OF_DATA * w)

  expectation = count * stats.dirichlet.mean(alpha + obs)
  stddev = count * np.sqrt(stats.dirichlet.var(alpha + obs))

  return expectation, stddev

def posterior_orth(w, obs_w, obs_d):

  count = obs_w.sum() # == obs_d.sum()

  w_exp, w_sd = posterior(w, obs_w)
  d_exp, d_sd = posterior(w, obs_d)

  w_var = (w_sd / count) ** 2
  d_var = (d_sd / count) ** 2

  var = np.tile(d_var, 7) + np.repeat(w_var, 3)

  expectation = np.reshape(np.outer(w_exp / w_exp.sum(), d_exp / d_exp.sum()), 21) * obs_w.sum()
  # add variances?
  stddev = count * np.sqrt(var)
  return expectation, stddev


def plot(name, weight, ax, obs, expectation, stddev):
  ax.bar(x, obs, width=0.5, alpha=1.0, label="Observed events")
  ax.errorbar(x, expectation, fmt='o', yerr=stddev, color="r", label="Posterior distribution")
  ax.fill_between(x, expectation-stddev, expectation+stddev, alpha=0.2, color="orange")
  ax.set_xticklabels(x, rotation=90, ha='right')
  #ax.set_title("Prior weight=%.1f/y Samples=%.1f/y" % (weight, np.sum(obs)/YEARS_OF_DATA))
  ax.set_title(name)

# no of categories
YEARS_OF_DATA = 2

data = decrypt_csv("./data/weekly-weights.csv.enc", index_col=["xcor_code", "period"])

# data_w = pd.read_csv("./weekly_adjusted.csv", index_col=["xcor_code", "DayNumber"])
# data_d = pd.read_csv("./daily_adjusted.csv", index_col=["xcor_code", "TimeWindow"])

#plt.tight_layout()

#types = ["1", "10A", "17B", "22B", "30C", "8R", "105A"]
names = pd.read_csv("./data/policeuk-ons-code-join.csv")[["ONS_COUNTS_description", "ONS_COUNTS_code"]]
#names = pd.read_csv("./data/policeuk-ons-code-join.csv")[["ONS_COUNTS_description", "ONS_COUNTS_code"]]
#names = pd.read_csv("../crims/data/police-uk-category-mappings.csv")[["Home Office Code", "Offence"]]
types = data.index.unique(level=0).values

# TODO investigate code mismatch
types2 = names.ONS_COUNTS_code .unique()
print("Codes with no description: %s" % np.setdiff1d(types, types2))

#print(np.setdiff1d(types2, types))
# ['100' '200' '37/2' '4.10' '5550' '8T' '8U' 'NFIB1']
# ['1/4.1/4.10/4.2' '14' '15' '27' '28D' '31' '37.1' '37.2' '3A' '4.2' '4.3' '4.6' '4.9' '72' '90']

for ctype in types:

  obs = data.loc[ctype, "count"]

  print(ctype)

  try:
    name = names[names.ONS_COUNTS_code == ctype].ONS_COUNTS_description.values[0]
  except:
    print("no description for %s" % ctype)
    continue
  #axs[i].suptitle("%s (%s)" % (name, ctype))

  # weight prior so that total samples at least 1 per week
  w = max(52.0 - obs.sum()/2, 1.0) # per year

  # or... how do we compute variance?
  #obs_w = data_w.loc[ctype, "count"]
  #obs_d = data_d.loc[ctype, "count"]

  expectation, stddev = posterior(w, obs)
  #expectation, stddev = posterior_orth(w, obs_w, obs_d)

  #plot("%s (%s)" % (name, ctype), w, axs[i], obs, expectation, stddev)

  plt.cla()
  plt.bar(x, obs, label="Observed", alpha=0.5)
  plt.errorbar(x, expectation, fmt='o', yerr=stddev, color="r", label="Posterior distribution")
  plt.fill_between(x, expectation-stddev, expectation+stddev, alpha=0.2, color="orange")
  #plt.plot(x, p["count_adj2"], "o", label="posterior (orthogonal)", color="orange")
  #plt.plot(x, [1/3]*len(x), "o", label="prior", color="k",markersize=2)
  plt.xticks(rotation = 60) # Rotates X-Axis Ticks by 45-degrees
  plt.title("%s (code=%s count=%.1f/y prior weight=%.1f/y)" % (name, ctype, obs.sum()/2, w))
  plt.xlabel("8h period")
  plt.ylabel("count")
  plt.legend()

  plt.savefig("./doc/inference-%s.png" % ctype.replace("/", "_"))
  #break

#plt.show()

# TODO pymc3 ? see here https://towardsdatascience.com/estimating-probabilities-with-bayesian-modeling-in-python-7144be007815
# and https://en.wikipedia.org/wiki/Categorical_distribution#Bayesian_inference_using_conjugate_prior
