
import os
from io import BytesIO
from pathlib import Path
import pandas as pd
from cryptography.fernet import Fernet

# based on https://devqa.io/encrypt-decrypt-data-python/
# and https://towardsdatascience.com/encrypting-your-data-9eac85364cb

def _get_key():
  key_file = os.getenv("CRIMS_ENCRYPTION_KEY")
  if key_file is None:
    raise EnvironmentError("CRIMS_ENCRYPTION_KEY not set")
  if not Path(key_file).is_file():
    raise FileNotFoundError("Key file not found")
  with open(key_file, 'rb') as fd:
    key = fd.read()
  return key

def encrypt_csv(dataframe, filename, with_index=True):
  """ Encrypts a dataframe and saves to filesystem in csv format """

  print(dataframe.head())

  data = BytesIO()
  dataframe.to_csv(data, index=with_index)

  fernet = Fernet(_get_key())
  encrypted = fernet.encrypt(data.getvalue())

  # Write the encrypted file
  with open(filename, 'wb') as fd:
    fd.write(encrypted)

def decrypt_csv(data_file):
  """ Loads a dataframe from an encrypted csv file """

  with open(data_file, 'rb') as f:
    encrypted = f.read()

  fernet = Fernet(_get_key())
  data = fernet.decrypt(encrypted)

  df = pd.read_csv(BytesIO(data))

  return df
