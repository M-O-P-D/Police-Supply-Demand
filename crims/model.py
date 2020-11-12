import numpy as np
import pandas as pd
import neworder as no
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .crime import Crime
from .utils import smooth
from .streamer import DataStream

class CrimeMicrosim(no.Model):
  def __init__(self, start_year, end_year, force_area):
    # timeline with monthly steps and annual checkpoints
    timeline = no.Timeline(start_year, end_year, [(n+1-start_year)*12 for n in range(start_year, end_year)])
    super().__init__(timeline, lambda _: 14)

    crime = Crime(force_area, 2017, 10, 2020, 9)
    self.crime_rates = crime.get_crime_counts()
    self.crime_outcomes = crime.get_crime_outcomes()

    self.crime_types = self.crime_rates.index.unique(level=1)
    self.geogs = self.crime_rates.index.unique(level=0)

    self.crimes = self.__sample_crimes()

    # upstream model
    self.datastream = DataStream("http://localhost:5000")

  def step(self):

    # get year and month
    start_y = int(self.timeline().start() + (self.timeline().index()-1) // 12)
    start_m = (self.timeline().index()-1) % 12 + 1

    start_date = datetime(year=start_y, month=start_m, day=1)
    end_date = start_date + relativedelta(months=1)

    # send monthly data to upstream model - if its listening
    adjustments = self.datastream.send_recv(self.crimes[(self.crimes.time >= start_date) & (self.crimes.time < end_date)])

    no.log("%d-%d: %d crimes. posted: %s" % (start_y, start_m, len(self.crimes[(self.crimes.time >= start_date) & (self.crimes.time < end_date)]), adjustments is not None))

    if adjustments is not None:
      no.log("received %d adjustments" % len(adjustments))

  def __sample_crimes(self):
    # simulate 1 year of crimes from a non-homogeneous Poisson process using a lambda derived
    # from geographical and historical/seasonal incidence for each crime type

    # assumes time is year only
    offset = datetime(int(self.timeline().time()), 1, 1).timestamp()
    secs_year = datetime(int(self.timeline().time() + 1), 1, 1).timestamp() - offset

    crimes = pd.DataFrame()

    for g in self.geogs:
      for ct in self.crime_types:
        if self.crime_rates.index.isin([(g, ct)]).any():
          # smooth the data
          smoothed_rates = smooth(self.crime_rates.loc[(g, ct)].values, 7)
          lambdas = np.append(smoothed_rates, 0).astype(float)
          times = self.mc().arrivals(lambdas, 1/12, 1, 0.0)[0]
          p_suspect = self.crime_outcomes.loc[(g,ct), "pSuspect"]
          #print(p_suspect)
          if len(times) > 0:
            d = [datetime.fromtimestamp(t * secs_year + offset) for t in times]
            s = self.mc().hazard(p_suspect, len(times)).astype(bool)
            df = pd.DataFrame(index=range(len(d)), data={"MSOA": g, "crime_type": ct, "time": d, "suspect": s })
            crimes = crimes.append(df, ignore_index=True)

    return crimes.set_index(["MSOA", "crime_type"], drop=True)


  def checkpoint(self):
    # sample another year's worth of crimes unless we're done
    if not self.timeline().at_end():
      self.crimes = self.crimes.append(self.__sample_crimes())
    # no.log(self.crimes)
    # no.log(self.crime_rates.sum().mean())




