# Model Stacks

## Model Stack 1

The simplest implementation: a single process: NetLogo must run in the crims (virtual/conda)env in order to have the crims dependencies available.

The models interact in a lock-step manner with feedback: the microsimulation supplies crime data, and the ABM can alter the microsimulation parameters after each timestep to reflect it's own internal state. (e.g. alter the prevalence of certain crime types).

The NetLogo ABM, via the python plugin, initialises and runs the microsimulation model, which is set to halt after each timestep. Once the ABM has consumed the simulated crime data for that timestep, NetLogo signals to the model to resume execution (possibly providing altered sampling parameters).

TODO: At the moment the two models are in seaprate github repos, better integration would make life easier.

## Model Stack 2

(deprecated for now)

Separate processes:

- Netlogo police suppy ABM
- *neworder* crime microsimulation model

Each run as a standalone process. This allows them to run more efficiently as they can (in practice not?) each continue running while the other model is busy, but means that exchanging data is slightly more difficult.

When the NetLogo model is run, it requests the microsimulation to initialise, then *subscribes* to synthetic crime datasets produced by it. The microsimulation *subscribes* to parameter adjustments coming back from from the upstream ABM.

On initialisation, the microsimulation performs one timestep, *publishes* the synthetic crime dataset, and waits for a response.

Once received, it is consumed by the ABM until fully processed. The ABM can then *publish* adjustments/variations to the microsimulation parameters (e.g. making some crime types more or less probable) which the microsimulation incorporates in computing subsequent crime datasets.  and then awaits an updated dataset.

Communication between the two models is brokered by [*redis*](https://redis.io/), using its *pubsub* (publish-subscribe) functionality.

### Prerequisites

Assumes python 3 on system
#### Redis

See e.g. [https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-18-04](https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-18-04)

```bash
sudo apt install redis-server
```

#### NetLogo

Download netlogo from [here](https://ccl.northwestern.edu/netlogo/6.1.1/)

e.g. for linux use the script [get_netlogo.sh](../get_netlogo.sh)

### neworder

```bash
pip install neworder
```

### Run

```
./NetLogo\ 6.1.1/NetLogo
```
