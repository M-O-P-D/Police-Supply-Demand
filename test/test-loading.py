

import pandas as pd
import neworder as no
from crims import model

import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning, module=r'.*pyproj' )

start = (2021, 1)
force = "City of London"

# model will run for 12 months initially
model = model.CrimeMicrosim(0, force, start, burn_in=1)


model.set_loading(0.5)

model.set_loading(1.5, "anti-social behaviour")
model.set_loading(2.5, "burglary")
model.set_loading(2.0, "aggravated burglary residential")


print(model.get_loading("anti-social behaviour"))
print(model.get_loading("ANti-SOCial behaviouR"))
#print(model.get_loading("bicycle theft"))
print(model.get_loading("theft or unauthorised taking of a pedal cycle"))

print(model.loading_factors)