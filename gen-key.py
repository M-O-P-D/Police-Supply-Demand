# from https://devqa.io/encrypt-decrypt-data-python/

from pathlib import Path
from cryptography.fernet import Fernet

def generate_key(envvar):
  key = Fernet.generate_key()
  print("%s=%s" % (envvar, key.decode("utf-8")))

if __name__ == "__main__":
  envvar="CRIMS_ENCRYPTION_KEY"
  generate_key(envvar)
