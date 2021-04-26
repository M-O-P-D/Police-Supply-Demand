
import numpy as np
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

  print(alpha)
  print(obs)

  expectation = count * stats.dirichlet.mean(alpha + obs)

  stddev = count * np.sqrt(stats.dirichlet.var(alpha + obs))

  return expectation, stddev

def plot(ctype, weight, ax, obs, expectation, stddev):
  ax.bar(x, obs, width=0.5, alpha=1.0, label="Observed events")
  ax.errorbar(x, expectation, fmt='o', yerr=stddev, color="r", label="Posterior distribution")
  ax.fill_between(x, expectation-stddev, expectation+stddev, alpha=0.2, color="orange")
  ax.set_title("%s Prior weight=%.1f/y Samples=%.1f/y" % (ctype, weight, np.sum(obs)/YEARS_OF_DATA))

# no of categories
YEARS_OF_DATA = 2

data = decrypt_csv("./data/weekly-weights.csv.enc", index_col=["xcor_code", "period"])

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15,5))
plt.tight_layout()

#types = ["1", "10A", "17B", "22B", "30C", "8R", "105A"]
ctype = "17B"

obs = data.loc[ctype, "count"]

w = 1.0 # per year
expectation, stddev = posterior(w, obs)
plot(ctype, w, ax1, obs, expectation, stddev)

w = 4.0 # per year
expectation, stddev = posterior(w, obs)
plot(ctype, w, ax2, obs, expectation, stddev)

w = 16.0 # per year
expectation, stddev = posterior(w, obs)
plot(ctype, w, ax3, obs, expectation, stddev)

# ax1.bar(x, obs, width=0.5, alpha=1.0, label="Observed events")
# ax1.errorbar(x, expectation, fmt='o', yerr=stddev, color="r", label="Posterior distribution")
# ax1.fill_between(x, expectation-stddev, expectation+stddev, alpha=0.2, color="orange")
# ax1.set_title("Prior weight=%d Samples=%d" % (w*K, N))


plt.show()

# TODO pymc3 ? see here https://towardsdatascience.com/estimating-probabilities-with-bayesian-modeling-in-python-7144be007815
# and https://en.wikipedia.org/wiki/Categorical_distribution#Bayesian_inference_using_conjugate_prior
