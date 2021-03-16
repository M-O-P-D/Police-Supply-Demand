
import pandas as pd
import neworder as no

from crims.visualisation import density_map
from crims.model import CrimeMicrosim

if __name__ == "__main__":

  force="City of London"
  month=2

  model = CrimeMicrosim(force, (2020, month), (2020, month+1))
  no.run(model)

  crimes = model.crimes
  print(crimes.head())

  plt = density_map(crimes, force)
  plt.show()