# from https://devqa.io/encrypt-decrypt-data-python/
# and https://towardsdatascience.com/encrypting-your-data-9eac85364cb


from io import BytesIO
from pathlib import Path
import pandas as pd
from cryptography.fernet import Fernet

def decrypt(key_file, data_file):
  with open(key_file, 'rb') as fd:
    key = fd.read()

  with open(data_file, 'rb') as f:
    encrypted = f.read()

  # #  Open the file to encrypt
  # with open(data_file, 'rb') as f:
  #   data = f.read()

  fernet = Fernet(key)
  data = fernet.decrypt(encrypted)

  df = pd.read_csv(BytesIO(data))

  print(df.head())

  # # Write the encrypted file
  # with open(data_file + ".enc", 'wb') as f:
  #     f.write(encrypted)

if __name__ == "__main__":
  key_file="encryption.key"
  data_file="data/weekly-weights.csv.enc"

  if not Path(key_file).is_file():
    print("Key not found")
  elif not Path(data_file).is_file():
    print("Data file not found")
  else:
    decrypt(key_file, data_file)
