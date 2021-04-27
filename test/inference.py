
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

  #print(c.head())
  count = obs.sum()
  alpha = np.full(len(obs), YEARS_OF_DATA * w / 3.0)

  #print(alpha)
  #print(obs)

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


def plot(ctype, weight, ax, obs, expectation, stddev):
  ax.bar(x, obs, width=0.5, alpha=1.0, label="Observed events")
  ax.errorbar(x, expectation, fmt='o', yerr=stddev, color="r", label="Posterior distribution")
  ax.fill_between(x, expectation-stddev, expectation+stddev, alpha=0.2, color="orange")
  ax.set_xticklabels(x, rotation=90, ha='right')
  ax.set_title("%s Prior weight=%.1f/y Samples=%.1f/y" % (ctype, weight, np.sum(obs)/YEARS_OF_DATA))

# no of categories
YEARS_OF_DATA = 2

data = decrypt_csv("./data/weekly-weights.csv.enc", index_col=["xcor_code", "period"])

data_w = pd.read_csv("./weekly_adjusted.csv", index_col=["xcor_code", "DayNumber"])
data_d = pd.read_csv("./daily_adjusted.csv", index_col=["xcor_code", "TimeWindow"])


fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15,5))
#plt.tight_layout()

#types = ["1", "10A", "17B", "22B", "30C", "8R", "105A"]
ctype = "17B"

obs = data.loc[ctype, "count"]

w = 1.0 # per year

# or... how do we compute variance
obs_w = data_w.loc[ctype, "count"]
obs_d = data_d.loc[ctype, "count"]

expectation, stddev = posterior(w, obs)
#expectation, stddev = posterior_orth(w, obs_w, obs_d)

# print(exp.sum())
# print(expectation.sum())
# print(std.sum())
# print(stddev.sum())
# print(std)
# print(stddev)
# stop
plot(ctype, w, ax1, obs, expectation, stddev)

w = 4.0 # per year
expectation, stddev = posterior(w, obs)
#expectation, stddev = posterior_orth(w, obs_w, obs_d)
plot(ctype, w, ax2, obs, expectation, stddev)

w = 16.0 # per year
expectation, stddev = posterior(w, obs)
#expectation, stddev = posterior_orth(w, obs_w, obs_d)
plot(ctype, w, ax3, obs, expectation, stddev)

# ax1.bar(x, obs, width=0.5, alpha=1.0, label="Observed events")
# ax1.errorbar(x, expectation, fmt='o', yerr=stddev, color="r", label="Posterior distribution")
# ax1.fill_between(x, expectation-stddev, expectation+stddev, alpha=0.2, color="orange")
# ax1.set_title("Prior weight=%d Samples=%d" % (w*K, N))


plt.show()

# TODO pymc3 ? see here https://towardsdatascience.com/estimating-probabilities-with-bayesian-modeling-in-python-7144be007815
# and https://en.wikipedia.org/wiki/Categorical_distribution#Bayesian_inference_using_conjugate_prior
