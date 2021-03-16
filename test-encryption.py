
import pandas as pd
from pathlib import Path

from crims.encryption import encrypt_csv, decrypt_csv


if __name__ == "__main__":
  data_file="data/weekly-weights.csv"

  assert Path(data_file).is_file(), "Plaintext data file not found"

  df = pd.read_csv(data_file)
  print(df.head())
  encrypt_csv(df, data_file+".enc", False)

  data_file += ".enc"
  assert Path(data_file).is_file(), "Encrypted data file not found"

  decrypted_df = decrypt_csv(data_file)
  print(decrypted_df.head())

  # have to check columns separately due to float rounding errors
  assert decrypted_df["xcor_code"].equals(df["xcor_code"])
  assert decrypted_df["period"].equals(df["period"])
  assert decrypted_df["count"].equals(df["count"])
  assert decrypted_df["total"].equals(df["total"])
  assert (decrypted_df["weight"] - df["weight"]).abs().max() < 1e-15


