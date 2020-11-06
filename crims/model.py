import numpy as np
import pandas as pd
import neworder as no

from .crime import get_crime_counts

class CrimeMicrosim(no.Model):
  def __init__(self, timeline, force_area):
    super().__init__(timeline, no.MonteCarlo.nondeterministic_stream)

    self.crime_rates = get_crime_counts(force_area)

    no.log(self.crime_rates)

    self.crime_types = self.crime_rates.index.unique(level=1)
    self.geogs = self.crime_rates.index.unique(level=0)

    #self.crimes = pd.DataFrame()

    self.count = 0

  def step(self):
    self.crimes = self.__sample_crimes()


  def __sample_crimes(self):
    # simulate 1 year of crimes from a non-homogeneous Poisson process using a lambda derived 
    # from geographical and historical/seasonal incidence for each crime type

    # TODO how to account for zero incidences in historical data?

    crimes = pd.DataFrame()

    for g in self.geogs:
      for ct in self.crime_types:
        if self.crime_rates.index.isin([(g, ct)]).any():
          lambdas = np.append(self.crime_rates.loc[(g, ct)].values, 0).astype(float)
          t = self.timeline().time() + self.mc().arrivals(lambdas, 1/12, 1, 0.0)[0]
          if len(t) > 0:
            df = pd.DataFrame(index=range(len(t)), data={"MSOA": g, "Crime type": ct, "Time": t})
            crimes = crimes.append(df, ignore_index=True)

    return crimes.set_index(["MSOA", "Crime type"], drop=True)


  def checkpoint(self):
    no.log(self.crimes)
    no.log(self.crime_rates.sum().mean())




