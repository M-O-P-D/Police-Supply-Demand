# Batch: BehaviourSpace/Experiments


```bash
~/NetLogo\ 6.2.0/netlogo-headless.sh --model event-response-with-shifts.nlogo --setup-file experiments/test.xml
```

## Running on ARC4

You may need to manually install extensions e.g. pathdir. See [here](https://github.com/cstaelin/Pathdir-Extension#installation)

It uses the java SGE module as opposed to a conda package, as installing the latter breaks a dependency (with fiona)

It's done in the batch submission script, but to do it explicitly:

```bash
module load java
```

then run the command above to ensure it works.

To submit a job, adjust cores, memory and runtime (in the script) as necessary then:

```bash
qsub batch.sh
```

NB memory is the memory *per core*, and runtime is the *total* CPU time