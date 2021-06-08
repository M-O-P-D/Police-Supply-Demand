
import subprocess
#import filecmp
#from io import BytesIO

# TODO make NETLOGO_HOME an env var
NETLOGO="/home/az/NetLogo 6.2.0/netlogo-headless.sh"

BASELINE="test/regression-baseline.txt"


def test_regression():

  result = subprocess.run([NETLOGO, "--model", "event-response-with-shifts.nlogo", "--setup-file", "test/regression.xml"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  #result = subprocess.run(["ls", "-l", "crims"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  # print(result.returncode)
  # print(result.stdout)
  # print(result.stderr)

  assert result.returncode == 0
  assert len(result.stderr) == 0

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

  assert not diff
 

if __name__ == "__main__":
  test_regression()