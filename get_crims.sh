#!/bin/bash

files="model.py crime.py utils.py"

# need actual files not symlinks for Docker
mkdir -p crims
for file in $files; do
  cp ../crims/crims/$file crims
done

if [ ! -L data ]; then
  ln -s ../crims/data
fi