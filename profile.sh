#!/bin/bash

# first run with profiling enabled, sending output to a file:
python -m cProfile -o profile.out test/test-model.py

# ensure pyprof2calltree (pip) and kcachegrind (apt) are installed
pyprof2calltree -k -i profile.out

