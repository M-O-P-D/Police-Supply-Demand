
# %%

from crims import crime
import contextily as ctx

gdf = crime.get_neighbourhoods('west-yorkshire')

ax = gdf.plot(figsize=(10, 10), alpha=0.5, edgecolor='k')
ctx.add_basemap(ax)

# %%
crimes = crime.api.get_crimes_area(wypd.get_neighbourhood("BDT_KE").boundary)

cgdf = gpd.GeoDataFrame({"category": [c.category for c in crimes],
                         "geometry": [Point(float(c.location.longitude), float(c.location.latitude)) for c in crimes]},
                        crs = {"init": "epsg:4326" })
cgdf = cgdf.to_crs(epsg=3857)


cgdf.head()
cgdf.plot(ax=ax, color="red")
# %%

