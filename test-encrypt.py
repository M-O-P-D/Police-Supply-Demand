
import pandas as pd
from pathlib import Path

from crims.encryption import encrypt_csv


if __name__ == "__main__":
  data_file="data/weekly-weights.csv"

  if not Path(data_file).is_file():
    print("Data file not found")
  else:
    encrypt_csv(pd.read_csv(data_file), data_file+".enc", False)
