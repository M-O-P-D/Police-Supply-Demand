
import pandas as pd
import neworder as no

from .crime import get_crime_counts

class CrimeMicrosim(no.Model):
  def __init__(self, timeline, force_area):
    super().__init__(timeline, no.MonteCarlo.deterministic_identical_stream)

    self.crime_rates = get_crime_counts(force_area)

    #no.log(self.crime_rates)

    self.crimes = pd.DataFrame()

  def step(self):

    # 44386    12  E02006876  Violence and sexual offences  43.000000
    no.log(self.mc().arrivals([43.0, 0.0], 1/12, 1, 0.0))
    pass

  def checkpoint(self):
    pass



