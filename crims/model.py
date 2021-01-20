import numpy as np
import pandas as pd
import neworder as no
from datetime import date
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from .crime import Crime
#from .streamer import DataStream
from .utils import get_periodicity

class CrimeMicrosim(no.Model):
  def __init__(self, force_area, start, end=None, agg_mode=True):
    # timeline with monthly steps and annual checkpoints
    if end is not None:
      timeline = no.CalendarTimeline(date(start[0], start[1], 1), date(end[0], end[1], 1), 1, "m")
    else:
      timeline = no.CalendarTimeline(date(start[0], start[1], 1), 1, "m")
    super().__init__(timeline, no.MonteCarlo.nondeterministic_stream)

    # this controls whether the model yields to the caller after each timestep, or runs to the end (aggregrating all the data)
    self.__aggregate = agg_mode

    self.__force_area = force_area
    crime = Crime(self.__force_area, 2017, 12, 2020, 11)
    self.__crime_rates = crime.get_crime_counts()
    self.__crime_outcomes = crime.get_crime_outcomes()

    self.__crime_types = self.__crime_rates.index.unique(level=1)
    self.__geogs = self.__crime_rates.index.unique(level=0)
    self.__crime_categories = crime.get_category_breakdown()

    # loading factor for crime sampling
    # TODO make function of crime type
    self.__loading = 1.0

    # upstream model
    #self.datastream = DataStream("http://localhost:5000")

    self.crimes = pd.DataFrame()

  def step(self):

    if self.__aggregate:
      self.crimes = self.crimes.append(self.__sample_crimes().sort_values(by="time"))
    else:
      self.crimes = self.__sample_crimes().sort_values(by="time")
      # yield to calling process
      self.halt()

    # # TODO *assumes* monthly but timeline might not be
    # start_date = self.timeline().time()
    # end_date = start_date + relativedelta(months=1)

    # # send monthly data to upstream model - if its listening
    # adjustments = self.datastream.send_recv(self.crimes[(self.crimes.time >= start_date) & (self.crimes.time < end_date)])

    # no.log("%s-%s: %d crimes. posted: %s" % (start_date, end_date, len(self.crimes[(self.crimes.time >= start_date) & (self.crimes.time < end_date)]), adjustments is not None))

    # if adjustments is not None:
    #   no.log("received %d adjustments" % len(adjustments))

  def set_loading(self, f):
    self.__loading = f

  def force_area(self):
    return self.__force_area

  def __sample_crimes(self):
    # simulate crimes from a non-homogeneous Poisson process using a lambda derived
    # from geographical and historical/seasonal incidence for each crime type, with weekly and daily periodicities superimposed
    t = self.timeline().time()
    # NB Mo=0, Su=6
    start_weekday, days_in_month = monthrange(t.year, t.month)
    periods_in_day = 3 # night (0:00-8:00) day (8:00-4:00), evening (4:00-0:00)
    periods = days_in_month * periods_in_day
    # this is the time resolution of the lambdas in the nonhomogeneous Poisson process
    dt = self.timeline().dt() / periods
    secs_per_year = 365.2475 * 86400 # consistent with dt() implementation

    # force column ordering
    crimes = pd.DataFrame(columns=[])

    for ct in self.__crime_types:
      # cd = subcats.index.values
      # p = subcats.proportion.values
      # s = self.mc().sample(100, p)
      # print([d[i] for i in s])
      # extra [] to sure result is always a dataframe (even if 1 row)
      # see https://stackoverflow.com/questions/20383647/pandas-selecting-by-label-sometimes-return-series-sometimes-returns-dataframe
      subcats = self.__crime_categories.loc[[ct]]

      # print(subcats.proportion)
      # continue
      time_weights = get_periodicity(start_weekday, days_in_month, ct)

      for g in self.__geogs:
        if self.__crime_rates.index.isin([(g, ct)]).any():
          # impose daily/weekly periodicity to the monthly frequency and adjust by loading factor
          lambdas = self.__crime_rates.loc[(g, ct), ("count", "%02d" % t.month)] * time_weights * self.__loading
          # append extra zero element at end so don't sample into next timestep
          lambdas = np.append(lambdas, 0.0)
          times = self.mc().arrivals(lambdas, dt, 1, 0.0)[0]
          #no.log(times)
          p_suspect = self.__crime_outcomes.loc[(g,ct), "pSuspect"]
          #print(p_suspect)
          if len(times) > 0:
            d = [t + relativedelta(seconds=time*secs_per_year) for time in times]
            s = self.mc().hazard(p_suspect, len(times)).astype(bool)
            c = self.mc().sample(len(times), subcats.proportion.values)
            df = pd.DataFrame(index=range(len(d)), data={"MSOA": g,
                                                         "crime_type": ct,
                                                         "code": subcats.iloc[c]["code_original"].values,
                                                         "description": subcats.iloc[c]["description"].values,
                                                         "time": d,
                                                         "suspect": s,
                                                         "severity": subcats.iloc[c]["ONS_SEVERITY_weight"].values })
            crimes = crimes.append(df, ignore_index=True)

    # round to nearest minute
    crimes["time"] = crimes["time"].round("min")
    return crimes.set_index(["MSOA", "crime_type"], drop=True)


  def checkpoint(self):
    no.log("Simualated %d crimes between %s and %s" % (len(self.crimes), self.timeline().start(), self.timeline().end()))
    #no.log("Annual average = %f" % self.__crime_rates.sum().mean())
    #no.log(self.crimes)




