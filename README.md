# CriMS

Policing and Crime supply-demand modelling. *CriMS* is an evolution of **crime-sim-toolkit** <sup>[[6]](#references)</sup> and forms the microsynthesis and microsimulation components of this workflow:

![workflow](./doc/workflow.svg)

## Population Data

Uses the **ukcensusapi** <sup>[[1]](#references)</sup> and **ukpopulation** <sup>[[2]](#references)</sup> packages to generate MSOA-level population data derived from the 2011 census and scaled to 2020 subnational population projections.

## Crime Data

Uses the **police-api-client** <sup>[[3]](#references)</sup> and the **police open data portal** <sup>[[4]](#references)</sup> directly to get open data on crime occurrences.

## Model

![sample visualisation](./doc/wy2020.png)

Uses the **neworder** <sup>[[5]](#references)</sup> microsimulation framework to run the model. It uses historical data to determine counts of crimes as a function of location (MSOA), time (month), and (broad) type, so can capture seasonal fluctuations in crime frequency. It then imposes further weekly and daily periodicity to the crime rate, and this to sample crime incidences from a non-homogeneous Poisson process. More detailed crime types, and whether a suspect has been identified, are also sampled at force area resolution. This synthetic crime data can be fed into an agent-based model of Police operations which can alter its policies, potentially feeding back changes to crime rates that may result.

### Planned Model Enhancements

- [ ] Capture temporal trends in crime rates (as well as seasonality)
- [ ] Capture daily and weekly periodicity of crimes by crime type
- [ ] Alter crime incidence rates according to feedback from upstream model

## Data sources

- Bulk crime and outcome data, force boundaries: [data.police.uk](<https://data.police.uk>)

<!--- Sample (interim) victim data from **crime-sim-toolkit** <sup>[[6]](#references)</sup>-->

- MSOA (2011) boundaries: [geoportal.statistics.gov.uk](<https://geoportal.statistics.gov.uk/datasets/middle-layer-super-output-areas-december-2011-ew-bsc-v2>)

- [Detailed crime counts by classification](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/928924/prc-pfa-mar2013-onwards-tables.ods)

- [Crime severity scores](https://www.ons.gov.uk/peoplepopulationandcommunity/crimeandjustice/datasets/crimeseverityscoreexperimentalstatistics)

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

### `/map`

Takes 2 query params, `force` and `month`, and returns crime density by MSOA plotted on a map.

`http://localhost:5000/map?force=Devon%20and%20Cornwall&month=12`

This service is available as a docker image (due to its size and relatively infrequent changes, the data is in a separate image - which will take a while to initially download):

```
docker pull mopd/crims
docker run --rm -d  -p 80:5000/tcp mopd/crims
```
which runs it locally, listening for requestios on the default http port. You can then request data from the container, e.g. in python/pandas:

```
>>> import pandas as pd
>>> df1 = pd.read_csv("http://localhost/data?force=City%20of%20London&month=3&format=csv")
>>> df1.head()
        MSOA                    crime_type                                  description                 time  suspect
0  E02006924  violence and sexual offences  Sexual assault on a female aged 13 and over  2020-03-01 00:35:00    False
1  E02000001  violence and sexual offences                       Assault without injury  2020-03-01 02:09:00     True
2  E02000001                   other theft                                  Other theft  2020-03-01 02:37:00    False
3  E02000001                 vehicle crime             Interfering with a motor vehicle  2020-03-01 03:33:00    False
4  E02000001                   other theft                                  Other theft  2020-03-01 03:56:00    False
>>> df2 = pd.read_json("http://localhost/data?force=City%20of%20London&month=3", orient="table")
>>> df2.head()
        MSOA             crime_type                                description                time  suspect
0  E02000001  possession of weapons  Possession of article with blade or point 2020-03-01 00:09:00    False
1  E02000001            other theft                                Other theft 2020-03-01 00:44:00     True
2  E02000001          vehicle crime                         Theft from vehicle 2020-03-01 02:38:00    False
3  E02000001          vehicle crime                         Theft from vehicle 2020-03-01 05:28:00    False
4  E02000001               burglary            Burglary Business and Community 2020-03-01 06:39:00    False
>>>
```

## References

1. [ukcensusapi: UK census data query automation](<https://pypi.org/project/ukcensusapi/>)

2. [ukpopulation: UK Demographic Projections](<https://pypi.org/project/ukpopulation/>)

3. [police-api-client: Python client library for the Police API](<https://pypi.org/project/police-api-client/>)

4. [Police Open Data Portal](<https://data.police.uk/>)

<!--[4] [humanleague: Microsynthesis using quasirandom sampling and/or IPF](<https://pypi.org/project/humanleague/>)-->

5. [neworder: A dynamic microsimulation framework](<https://neworder.readthedocs.io>)

6. [crime-sim-toolkit](<https://github.com/M-O-P-D/crime_sim_toolkit>)