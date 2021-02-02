# from https://devqa.io/encrypt-decrypt-data-python/

from pathlib import Path
from cryptography.fernet import Fernet

def generate_key(filename):
  """
  Generates a key and save it into a file
  """
  key = Fernet.generate_key()
  with open(filename, "wb") as key_file:
    key_file.write(key)

if __name__ == "__main__":
  filename="encryption.key"

  if Path(filename).is_file():
    print("File exists, not generating new key")
  else:
    generate_key(filename)
