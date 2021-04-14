#!/bin/bash

#$ -m be
#$ -M a.p.smith@leeds.ac.uk
#$ -cwd -V
#$ -l h_vmem=2G
#$ -l h_rt=8:00:00
#$ -o log
#$ -e log
#$ -pe ib 10


# bail if no conda env activated
[[ -z $CONDA_DEFAULT_ENV ]] && { echo "No conda env activated, exiting"; exit 1; }

# check arg is file
[[ "$#" -ne "1" ]] && { echo "No experiment file specified, exiting"; exit 1; }
[[ -f "$1" ]] || { echo "Experiment file not found: $1"; exit 1; }

module load java/13.0.1

~/NetLogo\ 6.2.0/netlogo-headless.sh --model event-response-with-shifts.nlogo --setup-file $1

