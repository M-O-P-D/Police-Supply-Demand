
import os
from io import BytesIO
from pathlib import Path
import pandas as pd
from cryptography.fernet import Fernet

# based loosely on https://devqa.io/encrypt-decrypt-data-python/
# and https://towardsdatascience.com/encrypting-your-data-9eac85364cb

def _get_key():
  key = os.getenv("CRIMS_ENCRYPTION_KEY")
  if key is None:
    raise EnvironmentError("CRIMS_ENCRYPTION_KEY not set")
  return key

def encrypt_csv(dataframe, filename, with_index=True):
  """ Encrypts a dataframe and saves to filesystem in csv format """

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
