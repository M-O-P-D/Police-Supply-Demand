
# %%

import numpy as np
#from datetime import datetime, date
from calendar import monthrange

import matplotlib.pyplot as plt

from crims.utils import get_periodicity

year = 2020
month = 11 # starts on sun

start_dow, days_in_month = monthrange(year, month)


w = get_periodicity(start_dow, days_in_month, None)

assert np.fabs(np.mean(w) - 1.0) < 1e-8

plt.bar(np.linspace(1, days_in_month, 3*days_in_month), w, width=0.2)

plt.show()
# %%
