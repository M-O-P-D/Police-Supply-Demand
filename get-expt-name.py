#!/usr/bin/env python

import sys
from bs4 import BeautifulSoup

if __name__ == "__main__":

  assert len(sys.argv) == 2

  expt_filename = sys.argv[1]

  with open(expt_filename, 'r') as fd:
    xml = BeautifulSoup(fd.read(), 'html.parser')
  expt = xml.find_all("experiment")

  assert len(expt) == 1, "multiple experiments in file, don't know what to do"
  print(expt[0].get("name"))

