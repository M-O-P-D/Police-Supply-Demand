
import numpy as np
from scipy import stats

import matplotlib.pyplot as plt

# manual calculations
def mean(c, alpha):
  return (c + alpha) / (np.sum(c) + np.sum(alpha))

def var(c, alpha):
  s = np.sum(c + alpha)
  a = (c + alpha) / s
  return a * (1 - a) / (s + 1)

# no of categories
K = 12

#impose some periodicity to the sampling
ps = 4+np.sin(np.linspace(0.0, 2*np.pi, K+1)[:-1])
ps /= np.sum(ps)


def sample(K, w, N, ps):
  alpha = np.ones(K) * w + 1

  rng = np.random.default_rng()

  c = np.bincount(rng.choice(K, N, p=ps), minlength=K)
  #print(c)

  p = stats.dirichlet.mean(c + alpha)
  assert np.all(p == mean(c, alpha))
  #print(p)

  v = stats.dirichlet.var(c + alpha) #print(var(c, alpha))
  assert np.allclose(v, var(c, alpha), rtol=2**-53)
  #print(v)

  return c, p, np.sqrt(v)

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15,5))
#fig.suptitle('Horizontally stacked subplots')

# prior weight
w = 1.0
N = 12
c, p, sd = sample(K, w, N, ps)

ax1.bar(range(K), c, width=0.3, alpha=0.5, label="Sampled events")
ax1.errorbar(range(K), p*N, fmt='o', yerr=sd*N, color="r", label="Posterior distribution")
ax1.fill_between(range(K), (p-sd)*N, (p+sd)*N, alpha=0.2, color="orange")
ax1.plot(range(K), ps*N, color='k', alpha=0.5, label="Sample distribution")
ax1.set_title("Prior weight=%d Samples=%d" % (w*K, N))

w = 30.0
N = 40
c, p, sd = sample(K, w, N, ps)
ax2.bar(range(K), c, width=0.3, alpha=0.5)
ax2.errorbar(range(K), p*N, fmt='o', yerr=sd*N, color="r")
ax2.fill_between(range(K), (p-sd)*N, (p+sd)*N, color="orange", alpha=0.2)
ax2.plot(range(K), ps*N, color='k', alpha=0.5)
ax1.legend()
ax2.set_title("Prior weight=%d Samples=%d" % (w*K, N))

w = 30.0
N = 4000
c, p, sd = sample(K, w, N, ps)
ax3.bar(range(K), c, width=0.3, alpha=0.5)
ax3.errorbar(range(K), p*N, fmt='o', yerr=sd*N, color="r")
ax3.fill_between(range(K), (p-sd)*N, (p+sd)*N, color="orange", alpha=0.2)
ax3.plot(range(K), ps*N, color="k", alpha=0.5)
ax3.set_title("Prior weight=%d Samples=%d" % (w*K, N))
plt.show()

# TODO pymc3 ? see here https://towardsdatascience.com/estimating-probabilities-with-bayesian-modeling-in-python-7144be007815
# and https://en.wikipedia.org/wiki/Categorical_distribution#Bayesian_inference_using_conjugate_prior
