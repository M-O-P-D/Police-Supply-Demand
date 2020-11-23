# CriMS

Policing and Crime supply-demand modelling. *CriMS* is an evolution of **crime-sim-toolkit** [[6]] and forms the microsynthesis and microsimulation components of this workflow:

![workflow](./doc/workflow.svg)

## Population Data

Uses the **ukcensusapi** [[1]](#references) and **ukpopulation** [[2]](#references) packages to generate MSOA-level population data derived from the 2011 census and scaled to 2020 subnational population projections.

## Crime Data

Uses the **police-api-client** [[3]](#references) and the **police open data portal** directly [[4]](#references)  to get open data on crime occurrences and some closed data to sample victim characteristics.

## Model

![sample visualisation](./doc/wy2020.png)

Uses the **neworder** [[5]](#references) microsimulation framework to run the model. It uses historical data to determine counts of crimes as a function of location (MSOA), time (month), and type, so can capture seasonal fluctuations in crime frequency, and uses this data to simulate crime patterns as non-homogeneous Poisson processes. This crime data is to be fed into an agent-based model of Police operations which can alter its policies, potentially feeding back changes to crime rates that may result.

### Planned Model Enhancements

- Capture temporal trends in crime rates (as well as seasonality)
- Capture daily and weekly periodicity of crimes by crime type
- Alter crime incidence rates according to feedback from upstream model

## Data sources

- Bulk crime and outcome data, force boundaries: [data.police.uk](<https://data.police.uk>)

- Sample (interim) victim data from **crime-sim-toolkit** [[6]](#references)

- MSOA (2011) boundaries: [geoportal.statistics.gov.uk](<https://geoportal.statistics.gov.uk/datasets/middle-layer-super-output-areas-december-2011-ew-bsc-v2>)

## Usage

First install dependencies

```bash
pip install -r requirements.txt
```

The script `run_model.py` can be used to run the model on a single force area and plot some output. Change the force area by editing the script. Run it like so:

```bash
python run_model.py "West Yorkshire" 2020 2022
```

which will simulate crime occurrences for West Yorkshire Police for 3 years, from 1/1/2020 to 31/12/2022. Note that some the crime locations may not be within the force area.

## Output

The model produces simulated crime data in four variables:

- spatial: MSOA in which the crime occurred
- temporal: the time at which the crime occurred/was reported/was responded to. (TODO which?)
- categorical:
  - the type of the crime
  - whether a suspect has been identified

## App Service

Run

```
FLASK_APP=server.py flask run
```

which exposes an API at port 5000 with two endpoints:

### `/data`

Takes 2 query params, `force` and `month` plus an optional param `format` (which defaults to `json`), and returns one month's simulated crime data for a given force area, e.g.

`http://localhost:5000/data?force=Durham&month=7`

`http://localhost:5000/data?force=City%20of%20London&month=2&format=csv`

`http://localhost:5000/map?force=Devon%20and%20Cornwall&month=12`

this service will be packaged as a docker image shortly.

## References

[1] [ukcensusapi: UK census data query automation](<https://pypi.org/project/ukcensusapi/>)

[2] [ukpopulation: UK Demographic Projections](<https://pypi.org/project/ukpopulation/>)

[3] [police-api-client: Python client library for the Police API](<https://pypi.org/project/police-api-client/>)

[4] [Police Open Data Portal](<https://data.police.uk/>)

<!--[4] [humanleague: Microsynthesis using quasirandom sampling and/or IPF](<https://pypi.org/project/humanleague/>)-->

[5] [neworder: A dynamic microsimulation framework](<https://neworder.readthedocs.io>)

[6] [crime-sim-toolkit](<https://github.com/M-O-P-D/crime_sim_toolkit>)