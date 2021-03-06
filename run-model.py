#import pandas as pd
import neworder as no
import argparse

#import matplotlib.pyplot as plt

def main(force_name, start_year, start_month, end_year, end_month):

  from crims import model
  #from crims import geography
  #from crims import utils
  from crims import visualisation

  # construct and run the model
  microsim = model.CrimeMicrosim(force_name, (start_year, start_month), (end_year, end_month))
  no.run(microsim)

  plt = visualisation.density_map(microsim.crimes, force_name)

  plt.show()


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="run crims Microsimualation model")
  parser.add_argument("force_area", type=str, help="the Police Force Area to be simulated")
  parser.add_argument("start_year", type=int, help="the initial year of the simulation")
  parser.add_argument("start_month", type=int, help="the initial month of the simulation")
  parser.add_argument("end_year", type=int, help="the end year of the simulation")
  parser.add_argument("end_month", type=int, help="the end month of the simulation")
  args = parser.parse_args()

  main(args.force_area, args.start_year, args.start_month, args.end_year, args.end_month)
