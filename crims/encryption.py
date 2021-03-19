
import os
from io import BytesIO
import pandas as pd
from cryptography.fernet import Fernet

# based loosely on https://devqa.io/encrypt-decrypt-data-python/
# and https://towardsdatascience.com/encrypting-your-data-9eac85364cb
from dotenv import load_dotenv
load_dotenv()

# get key from environment (use .env file)
def _get_key():
  key = os.getenv("CRIMS_ENCRYPTION_KEY")
  if key is None:
    raise EnvironmentError("CRIMS_ENCRYPTION_KEY not set")
  return key

def encrypt_csv(dataframe, filename, **kwargs):
  """ Encrypts a csv format dataframe and saves to filesystem
      kwargs are passed to DataFrame.to_csv method
  """
  data = BytesIO()
  dataframe.to_csv(data, **kwargs)

  fernet = Fernet(_get_key())
  encrypted = fernet.encrypt(data.getvalue())

  # Write the encrypted file
  with open(filename, 'wb') as fd:
    fd.write(encrypted)

def decrypt_csv(data_file, **kwargs):
  """ Loads a dataframe from an encrypted csv file
      kwargs are passed to pandas.read_csv method
  """
  with open(data_file, 'rb') as f:
    encrypted = f.read()

  fernet = Fernet(_get_key())
  data = fernet.decrypt(encrypted)

  df = pd.read_csv(BytesIO(data), **kwargs)

  return df
