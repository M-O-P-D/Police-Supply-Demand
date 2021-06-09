
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
load_dotenv() # for NETLOGO_HOME


BASELINE="test/regression-baseline.txt"

def test_regression():

  netlogo_dir = os.getenv("NETLOGO_HOME")
  assert netlogo_dir, "NETLOGO_HOME is not set"
  netlogo = Path(netlogo_dir) / "netlogo-headless.sh"
  assert netlogo.is_file(), "%s not found, check NETLOGO_HOME is set correctly" % netlogo

  result = subprocess.run([str(netlogo), "--model", "event-response-with-shifts.nlogo", "--setup-file", "test/regression.xml"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  assert result.returncode == 0, "Script returned error code: %d" % result.returncode
  assert len(result.stderr) == 0, "Script generated errors:\n%s" % result.stderr

  # skip blank at end
  output = result.stdout.decode("utf-8").split("\n")[:-1]

  with open(BASELINE) as fd:
    ref = fd.read().splitlines()

  diff = len(output) != len(ref)

  for i in range(min(len(output), len(ref))):
    if output[i] != ref[i]:
      diff = True
      print("Diff in line %d\n< %s\n> %s" % (i + 1, output[i], ref[i]))

  if diff:
    print("Differences detected, updating %s" % BASELINE)
    with open (BASELINE, "wb") as fd:
      fd.write(result.stdout)

  assert not diff, "Files differ - check and update if necessary"


if __name__ == "__main__":
  test_regression()