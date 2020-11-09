import numpy as np
import pandas as pd
import neworder as no
from datetime import datetime
from .crime import Crime
from .utils import smooth

class CrimeMicrosim(no.Model):
  def __init__(self, timeline, force_area):
    super().__init__(timeline, no.MonteCarlo.nondeterministic_stream)

    crime = Crime(force_area, 2019, 10, 2020, 9)
    self.crime_rates = crime.get_crime_counts()
    self.crime_outcomes = crime.get_crime_outcomes()
    print(self.crime_outcomes.index.levels[1].unique())
    print(self.crime_outcomes)

    self.crime_types = self.crime_rates.index.unique(level=1)
    self.geogs = self.crime_rates.index.unique(level=0)

    self.count = 0

  def step(self):
    self.crimes = self.__sample_crimes()


  def __sample_crimes(self):
    # simulate 1 year of crimes from a non-homogeneous Poisson process using a lambda derived 
    # from geographical and historical/seasonal incidence for each crime type

    # assumes time is year only
    offset = datetime(int(self.timeline().time()), 1, 1).timestamp()
    secs_year = datetime(int(self.timeline().time() + 1), 1, 1).timestamp() - offset

    # TODO add (broad) outcome/demand...

    crimes = pd.DataFrame()

    for g in self.geogs:
      for ct in self.crime_types:
        if self.crime_rates.index.isin([(g, ct)]).any():
          # smooth the data
          smoothed_rates = smooth(self.crime_rates.loc[(g, ct)].values, 7)
          lambdas = np.append(smoothed_rates, 0).astype(float)
          times = self.mc().arrivals(lambdas, 1/12, 1, 0.0)[0]
          # TODO when have geog in outcome data
          #p_suspect = self.crime_outcomes.loc[(g,ct), "weight"]
          #print(p_suspect)
          if len(times) > 0:
            d = [datetime.fromtimestamp(t * secs_year + offset) for t in times]
            #s = 
            df = pd.DataFrame(index=range(len(d)), data={"MSOA": g, "Crime type": ct, "Time": d, "SuspectDemand": None })
            crimes = crimes.append(df, ignore_index=True)

    return crimes.set_index(["MSOA", "Crime type"], drop=True)


  def checkpoint(self):
    no.log(self.crimes)
    no.log(self.crime_rates.sum().mean())




