
import numpy as np
from scipy import stats

import matplotlib.pyplot as plt

# no of categories
K = 12
# prior weight
w = 30.0

# no of data points to sample
N = 4000

alpha = np.ones(K) * w + 1
#print(alpha)

rng = np.random.default_rng()

# manual calculations
def mean(c, alpha):
  return (c + alpha) / (np.sum(c) + np.sum(alpha))

def var(c, alpha):
  s = np.sum(c + alpha)
  a = (c + alpha) / s
  return a * (1 - a) / (s + 1)

c = np.bincount(rng.choice(K, N), minlength=K)

#print(c)

p = stats.dirichlet.mean(c+alpha)
assert np.all(p == mean(c, alpha))
#print(p)

v = stats.dirichlet.var(c + alpha) #print(var(c, alpha))  
assert np.allclose(v, var(c, alpha), rtol=2**-53)
#print(var(c, alpha)-v)
#print(v)

plt.bar(range(K), c)
plt.errorbar(range(K), p*N, fmt='.', yerr=2*v*N, color="r")
#plt.plot(range(K), (p+v)*N)

plt.show()
#print(list(zip((p-v)*N, (p+v)*N)))
  
# TODO pymc3 ? see here https://towardsdatascience.com/estimating-probabilities-with-bayesian-modeling-in-python-7144be007815
# and https://en.wikipedia.org/wiki/Categorical_distribution#Bayesian_inference_using_conjugate_prior
