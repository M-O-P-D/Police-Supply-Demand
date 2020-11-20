import numpy as np
import pandas as pd
import neworder as no
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from .crime import Crime
from .streamer import DataStream

no.verbose()

class CrimeMicrosim(no.Model):
  def __init__(self, start_year, end_year, force_area):
    # timeline with monthly steps and annual checkpoints
    timeline = no.CalendarTimeline(date(start_year, 1, 1), date(end_year, 1, 1), 1, "m", end_year-start_year)
    no.log(timeline)
    super().__init__(timeline, lambda _: 14)

    crime = Crime(force_area, 2017, 10, 2020, 9)
    self.crime_rates = crime.get_crime_counts()
    self.crime_outcomes = crime.get_crime_outcomes()

    self.crime_types = self.crime_rates.index.unique(level=1)
    self.geogs = self.crime_rates.index.unique(level=0)
    self.crime_categories = crime.get_category_breakdown()

    # upstream model
    self.datastream = DataStream("http://localhost:5000")

  def step(self):

    # ensure we have crimes to sample to start with (this could be done in ctor but that would understimate reported exec time)
    if self.timeline().index() == 0: self.crimes = self.__sample_crimes()

    # TODO *assumes* monthly but timeline might not be
    start_date = self.timeline().start()
    end_date = start_date + relativedelta(months=1)

    # send monthly data to upstream model - if its listening
    adjustments = self.datastream.send_recv(self.crimes[(self.crimes.time >= start_date) & (self.crimes.time < end_date)])

    no.log("%s-%s: %d crimes. posted: %s" % (start_date, end_date, len(self.crimes[(self.crimes.time >= start_date) & (self.crimes.time < end_date)]), adjustments is not None))

    if adjustments is not None:
      no.log("received %d adjustments" % len(adjustments))

  def __sample_crimes(self):
    # simulate 1 year of crimes from a non-homogeneous Poisson process using a lambda derived
    # from geographical and historical/seasonal incidence for each crime type

    # assumes time is year only
    offset = self.timeline().time().timestamp()
    secs_year = (self.timeline().time() + relativedelta(years=1)).timestamp() - offset

    crimes = pd.DataFrame()

    for ct in self.crime_types:
      subcats = self.crime_categories.loc[ct]
      # cd = subcats.index.values
      # p = subcats.proportion.values
      # s = self.mc().sample(100, p)
      # print([d[i] for i in s])

      for g in self.geogs:
        if self.crime_rates.index.isin([(g, ct)]).any():
          lambdas = np.append(self.crime_rates.loc[(g, ct)].values, 0).astype(float)
          times = self.mc().arrivals(lambdas, 1/12, 1, 0.0)[0]
          p_suspect = self.crime_outcomes.loc[(g,ct), "pSuspect"]
          #print(p_suspect)
          if len(times) > 0:
            d = [datetime.fromtimestamp(t * secs_year + offset) for t in times]
            s = self.mc().hazard(p_suspect, len(times)).astype(bool)
            c = self.mc().sample(len(times), subcats.proportion.values) #/sum(subcats.proportion.values))
            df = pd.DataFrame(index=range(len(d)), data={"MSOA": g, "crime_type": ct, "description": subcats.iloc[c].index.values, "time": d, "suspect": s })
            crimes = crimes.append(df, ignore_index=True)

    return crimes.set_index(["MSOA", "crime_type"], drop=True)


  def checkpoint(self):
    # sample another year's worth of crimes unless we're done
    if not self.timeline().at_end():
      self.crimes = self.crimes.append(self.__sample_crimes())
    # no.log(self.crimes)
    # no.log(self.crime_rates.sum().mean())




