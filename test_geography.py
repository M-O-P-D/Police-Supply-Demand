
from crims import geography
import contextily as ctx


import matplotlib.pyplot as plt

force_boundaries = geography.create_forces_gdf()

print(force_boundaries.head())

ax = force_boundaries[force_boundaries.force == "west-yorkshire"].plot(figsize=(10, 10), alpha=0.3, edgecolor='k')

msoas = geography.get_msoa11_gdf()
print(msoas.head())
msoas.plot(ax=ax)
ctx.add_basemap(ax)

plt.show()