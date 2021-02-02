# from https://devqa.io/encrypt-decrypt-data-python/
# and https://towardsdatascience.com/encrypting-your-data-9eac85364cb

from io import BytesIO
import pandas as pd
from pathlib import Path
from cryptography.fernet import Fernet

def encrypt(key_file, dataframe):
  with open(key_file, 'rb') as fd:
    key = fd.read()

  print(dataframe.head())

  data = BytesIO()
  dataframe.to_csv(data, index=False)

  fernet = Fernet(key)
  encrypted = fernet.encrypt(data.getvalue())

  # Write the encrypted file
  with open(data_file + ".enc", 'wb') as f:
      f.write(encrypted)

if __name__ == "__main__":
  key_file="encryption.key"
  data_file="data/weekly-weights.csv"

  if not Path(key_file).is_file():
    print("Key not found")
  elif not Path(data_file).is_file():
    print("Data file not found")
  else:
    encrypt(key_file, pd.read_csv(data_file))
