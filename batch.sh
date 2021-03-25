#!/bin/bash

#$ -m be
#$ -M a.p.smith@leeds.ac.uk
#$ -cwd -V
#$ -l h_vmem=4G
#$ -l h_rt=1:00:00
#$ -o log
#$ -e log
#$ -pe ib 20

module load java

~/NetLogo\ 6.2.0/netlogo-headless.sh --model event-response-with-shifts.nlogo --setup-file experiments/test-batch.xml

