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
  def __init__(self, run_no, force_area, start, end=None, agg_mode=True):
    # timeline with monthly steps and annual checkpoints
    if end is not None:
      timeline = no.CalendarTimeline(date(start[0], start[1], 1), date(end[0], end[1], 1), 1, "m")
    else:
      timeline = no.CalendarTimeline(date(start[0], start[1], 1), 1, "m")
    super().__init__(timeline, lambda _: run_no + 77027465) # don't use with MPI - unless you want perfectly correlated streams!

    # this controls whether the model yields to the caller after each timestep, or runs to the end (aggregating all the data)
    self.__aggregate = agg_mode

    self.__force_area = force_area
    crime = Crime(self.__force_area, 2017, 12, 2020, 11)
    self.__crime_rates = crime.get_crime_counts()
    self.__crime_outcomes = crime.get_crime_outcomes()

    self.__crime_categories = self.__crime_rates.index.unique(level=1)
    self.__geogs = self.__crime_rates.index.unique(level=0)
    self.__crime_types = crime.get_category_breakdown()

    # loading factor for crime sampling
    # TODO make function of crime type
    self.__loading = dict.fromkeys(self.__crime_categories, 1.0)

    # upstream model
    #self.datastream = DataStream("http://localhost:5000")

    self.crimes = pd.DataFrame()

  def step(self):

    crimes = self.__sample_crimes().sort_values(by="time")
    no.log("Sampled %d crimes in month beginning %s" % (len(crimes), self.timeline().time()))
    if self.__aggregate:
      self.crimes = self.crimes.append(crimes)
    else:
      self.crimes = crimes
      # yield to calling process
      self.halt()

  def set_loading(self, f, category=None):
    if category is None:
      # change all values
      self.__loading = dict.fromkeys(self.__loading, f)
    else:
      # change specific value
      self.__loading[category] = f

  def get_loading(self):
    return self.__loading

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

    for cat in self.__crime_categories:

      # extra [] to ensure result is always a dataframe (even if 1 row)
      # see https://stackoverflow.com/questions/20383647/pandas-selecting-by-label-sometimes-return-series-sometimes-returns-dataframe
      crime_types = self.__crime_types.loc[[cat]]

      for _, crime_type in crime_types.iterrows():
        time_weights = get_periodicity(start_weekday, days_in_month, crime_type.code_original) * crime_type.proportion
        for g in self.__geogs:
          if self.__crime_rates.index.isin([(g, cat)]).any():
            intensity = self.__crime_rates.loc[(g, cat), ("count", "%02d" % t.month)]
            # only have suspect likelihood for broad category
            p_suspect = self.__crime_outcomes.loc[(g,cat), "pSuspect"]

            # impose daily/weekly periodicity of the subtype to the scaled intensity for the type, and adjust by loading factor
            lambdas = intensity * time_weights * self.__loading[cat]
            lambdas = np.append(lambdas, 0.0)
            times = self.mc().arrivals(lambdas, dt, 1, 0.0)[0]
            if len(times) > 0:
              d = [t + relativedelta(seconds=time*secs_per_year) for time in times]
              s = self.mc().hazard(p_suspect, len(times)).astype(bool)
              df = pd.DataFrame(index=no.df.unique_index(len(d)), data={"MSOA": g,
                                                          "crime_category": cat,
                                                          "code": crime_type.code_original,
                                                          "description": crime_type.description,
                                                          "time": d,
                                                          "suspect": s,
                                                          "severity": crime_type.ONS_SEVERITY_weight })
              crimes = crimes.append(df)

    # round to nearest minute
    crimes.index.name = "id"
    crimes["time"] = crimes["time"].round("min")
    return crimes


  def checkpoint(self):
    no.log("Simualated %d crimes between %s and %s" % (len(self.crimes), self.timeline().start(), self.timeline().end()))
    #no.log("Annual average = %f" % self.__crime_rates.sum().mean())
    #no.log(self.crimes)




