
from pykml import parser
from shapely.geometry import Polygon
import geopandas as gpd
import pandas as pd
import numpy as np
from zipfile import ZipFile
from .utils import get_data_path


def _kml2polygon(kml_file):
  polystring = parser.fromstring(kml_file).Document.Placemark.MultiGeometry.Polygon.outerBoundaryIs.LinearRing.coordinates.text
  polygon = Polygon(np.array([p.split(",") for p in polystring.split(" ")])[:, :2].astype(float))
  return polygon


def create_forces_gdf():

  kml_file = get_data_path("force_kmls.zip")
  z = ZipFile(kml_file)

  # this approach is much faster than appending a dataframe (apparently)
  raw = []
  for force in z.namelist():
    f = z.read(force)
    polygon = _kml2polygon(f)
    raw.append({"force": force.split("/")[1][:-4], "geometry": polygon})

  return gpd.GeoDataFrame(raw, crs={"init": "epsg:4326"}).to_crs(epsg=3785)  # .set_index("force", drop=True)


def filter_by_lads(df, column, lad_names):
  ret = pd.DataFrame()
  for lad_name in lad_names:
    ret = ret.append(df[df[column].str.startswith(lad_name)])
  return ret


def filter_by_list(df, column, msoa_list):
  return df[df[column].isin(msoa_list)]


def get_msoa11_gdf():
  # converts northing/eastings to webmercator
  msoa_file = "Middle_Layer_Super_Output_Areas__December_2011__EW_BSC_V2"
  msoa_data = gpd.read_file("zip://data/%s-shp.zip!%s.shp" % (msoa_file, msoa_file), crs={"init": "epsg:27700"}).to_crs(epsg=3785)
  return msoa_data
