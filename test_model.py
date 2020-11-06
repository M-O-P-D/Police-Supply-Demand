import neworder as no
from crims import model

no.verbose()

timeline = no.Timeline(2020,2021,[12])
model = model.CrimeMicrosim(timeline, "west-yorkshire")


no.run(model)

