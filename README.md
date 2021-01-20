# Police-Supply-Demand

## CriMS integration

~~1. clone the *M-O-P-D/crims* repo if you don't have it already, or ensure it's up-to-date
2. run the script `get_crims.py` (it assumes crims and this repo have a common parent directory)
4. initialise your python (3) environment (ideally use a virtualenv) - `pip install -r requirements.txt`
5. ensure the python integration is working by running `python netlogo_adapter.py`. You should get some crimes displayed (and no errors)
6. start netlogo (from within your virtualenv if you're using one)
7. run the netlogo model~~

Run the netlogo model from the crims repo (where this repo is now a submodule). See [here](https://github.com/M-O-P-D/crims/blob/master/doc/stack.md) for instructions.
## Docker container

**DEPRECATED, now done [here](https://github.com/M-O-P-D/crims/blob/master/README.md#docker)**

Get it from docker-hub:

```bash
docker pull mopd/police-supply-demand
```

Run it with permission to connect to the host's display manager:

```bash
xhost +
docker run --rm -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY mopd/police-supply-demand
```
