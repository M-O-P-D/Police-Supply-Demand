
from pathlib import Path
import pandas as pd

from crims.encryption import decrypt_csv

if __name__ == "__main__":
  data_file="data/weekly-weights.csv.enc"
  df = decrypt_csv(data_file)
  print(df.head())