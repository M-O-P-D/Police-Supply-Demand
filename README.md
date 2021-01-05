# Police-Supply-Demand

## CriMS integration

1. clone the M-O-P-D crims repo if you don't have it already, or ensure it's up-to-date
2. symlink the crims/crims subdirectory into this repo (so that you have `Police-Supply-Demand/crims`, containing `model.py`), e.g. `ln -s ../crims/crims`
3. symlink the crims/data subdirectory into this repo (so that you have `Police-Supply-Demand/data`)
4. initialise your python environment (ideally use a virtualenv) - `pip install -r requirements.txt`
5. ensure the python integration is working by running `python netlogo_adapter.py`. You should get some crimes displayed (and no errors)
6. start netlogo (from within your virtualenv if you're using one)
7. run the netlogo model