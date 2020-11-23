import pandas as pd
import neworder as no
import argparse
from crims import model
from crims import geography
from crims import utils
from crims import visualisation

#import matplotlib.pyplot as plt

def main(force_name, start_year, end_year):

  # construct and run the model
  microsim = model.CrimeMicrosim(start_year, end_year+1, force_name)
  no.run(microsim)

  plt = visualisation.density_map(microsim.crimes, force_name)

  plt.show()


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="run crims Microsimualation model")
  parser.add_argument("force_area", type=str, help="the Police Force Area to be simulated")
  parser.add_argument("start_year", type=int, help="the initial year of the simulation (from 1st Jan)")
  parser.add_argument("end_year", type=int, help="the final year of the simulation (to 31 Dec)")
  args = parser.parse_args()

  main(args.force_area, args.start_year, args.end_year)
