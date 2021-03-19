
import os
import pandas as pd
from pathlib import Path

from crims.encryption import encrypt_csv, decrypt_csv


if __name__ == "__main__":
  data_file="test/crime-sample.csv"

  assert Path(data_file).is_file(), "Plaintext data file not found"

  df = pd.read_csv(data_file, index_col="id")
  print(df.head())
  encrypt_csv(df, data_file+".enc")

  data_file += ".enc"
  assert Path(data_file).is_file(), "Encrypted data file not found"

  decrypted_df = decrypt_csv(data_file, index_col="id")
  print(decrypted_df.head())

  # have to check columns separately due to float rounding errors
  assert decrypted_df.index.equals(df.index)
  assert decrypted_df["MSOA"].equals(df["MSOA"])
  assert decrypted_df["crime_type"].equals(df["crime_type"])
  assert decrypted_df["code"].equals(df["code"])
  assert decrypted_df["description"].equals(df["description"])
  assert decrypted_df["time"].equals(df["time"])
  assert decrypted_df["suspect"].equals(df["suspect"])
  assert decrypted_df["severity"].equals(df["severity"])

  # remove the encrypted file
  os.remove(data_file)


