import math
import datetime
import os
import pyproj
import numpy as np

# Map Boundaries (area of interest)
lat_south = 53.5
lat_north = 54.6
lon_west = 7.2
lon_east = 9.5

# Maximum distance threshold (km)
max_distance_threshold = 1

# File Locations
data_prefix = os.path.join(os.path.split(os.path.dirname(os.path.abspath(__file__)))[0], "data")
tree_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trees", "allData")

sensors_suffix = "sensors.parquet"
timeline_suffix = "timeline.parquet"
trajectories_suffix = "trajectories.parquet"
sensor_metadata_suffix = "sensors_metadata.csv"
timeline_ranged_suffix = "timeline_ranged.parquet"
clustered_suffix = "clustered-10km.parquet"
range_dict_suffix = "rangedict.pickle"
path_sensors_db = os.path.join(data_prefix, sensors_suffix)
path_meta_db = os.path.join(data_prefix, sensor_metadata_suffix)
path_trajectories_db = os.path.join(data_prefix, trajectories_suffix)
path_time_db = os.path.join(data_prefix, timeline_suffix)
path_timeline_ranged_db = os.path.join(data_prefix, timeline_ranged_suffix)
path_clustered = os.path.join(data_prefix, clustered_suffix)
path_range_dict = os.path.join(data_prefix, range_dict_suffix)

# WGS -> Web
transformer_web = pyproj.Transformer.from_proj(proj_from=pyproj.Proj("EPSG:4326"), proj_to=pyproj.Proj("EPSG:3857"))


def WGS_to_Web(lon, lat):
    """
    Input: Longitude, Latitude in WGS 84 format.
    Output: x (Easting), y (Northing) in Web-Mercator format.
    """
    return transformer_web.transform(lat, lon)


# Web -> WGS
transformer_wgs = pyproj.Transformer.from_proj(proj_from=pyproj.Proj("EPSG:3857"), proj_to=pyproj.Proj("EPSG:4326"))


def Web_to_WGS(x, y):
    """
    Input: x (Easting), y (Northing) in Web-Mercator format.
    Output: Longitude, Latitude in WGS 84 format.
    """
    wgs = transformer_wgs.transform(x, y)
    return (wgs[1], wgs[0])


# Distances


def distance_wgs(lon1, lat1, lon2, lat2):
    """
    Haversine Distance for WGS84 coordinates:
    Calculate the great circle distance between two points
    on the earth.
    Input:  Longitude, Latitude of first point, then
            Longitude, Latitude of second point
    Output: Distance in kilometers
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    # Radius of earth in kilometers is 6371
    km = 6371 * c
    return km


def distance_web(x1, y1, x2, y2):
    """
    Haversine Distance for Web-Mercator coordinates (Wrapper).
    Calculate the great circle distance between two points
    on the earth.
    Input:  x, y of first point, then
            x, y of second point
    Output: Distance in kilometers
    """
    lon1, lat1 = Web_to_WGS(x1, y1)
    lon2, lat2 = Web_to_WGS(x2, y2)
    return distance_wgs(lon1, lat1, lon2, lat2)


class Region:
    """
    The Region object is used to define the spatial region in a query.
    The default region includes the entire area of interest in the
    WGS 84 coordinate system.
    Parameters:
    x_min : @TODO
    x_max :
    y_min :
    y_max :
    projection : "WGS" refers to float Longitude and Latitude input.
    """

    def __init__(self, x_min=lon_west, x_max=lon_east, y_min=lat_south, y_max=lat_north, projection="WGS"):
        self.projection = projection
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

        self.w = self.x_max - self.x_min
        self.h = self.y_max - self.y_min

    def wgs_to_web(self):
        self.projection = "Web"
        self.x_min, self.y_min = WGS_to_Web(self.x_min, self.y_min)
        self.x_max, self.y_max = WGS_to_Web(self.x_max, self.y_max)
        self.w = self.x_max - self.x_min
        self.h = self.y_max - self.y_min

    def web_to_wgs(self):
        self.projection = "WGS"
        self.x_min, self.y_min = Web_to_WGS(self.x_min, self.y_min)
        self.x_max, self.y_max = Web_to_WGS(self.x_max, self.y_max)
        self.w = self.x_max - self.x_min
        self.h = self.y_max - self.y_min

    def __copy__(self):
        return Region(self.x_min, self.x_max, self.y_min, self.y_max, self.projection)

    def __repr__(self):
        return str((self.x_min, self.x_max, self.y_min, self.y_max))

    def __str__(self):
        return f"({self.x_min:.2f}, {self.x_max:.2f}, {self.y_min:.2f}, {self.y_max:.2f})"

    def __eq__(self, other):
        return (
            (self.projection == other.projection)
            and (self.x_min == other.x_min)
            and (self.x_max == other.x_max)
            and (self.y_min == other.y_min)
            and (self.y_max == other.y_max)
        )

    def __getitem__(self, item):
        return [self.x_min, self.x_max, self.y_min, self.y_max]

    def contains(self, point):
        """Is point (a Point object or (x,y) tuple) inside this Rect?"""

        try:
            point_x, point_y = point.long, point.lat
        except AttributeError:
            point_x, point_y = point

        return point_x >= self.x_min and point_x < self.x_max and point_y >= self.y_min and point_y < self.y_max

    def intersects(self, other):
        """Does Region object other intersect this Region?"""
        return not (other.x_min > self.x_max or other.x_max < self.x_min or other.y_max < self.y_min or other.y_min > self.y_max)

    def to_rect(self):
        return [(self.y_min, self.x_min), (self.y_max, self.x_max)]


# Global instance of the default region.
default_region = Region()


class TimeSpan:
    """
    The TimeSpan object is used to define the timespan in a query.
    The default timespan includes all measurements.
    Parameters:
    start, end : in format datetime.datetime(year,month,day[,hour,minute,second])
    """

    def __init__(self, start: datetime.datetime = datetime.datetime(2000, 1, 1), end: datetime.datetime = datetime.datetime(2020, 1, 1)):
        self.start = start
        self.end = end

    def __copy__(self):
        return TimeSpan(self.start, self.end)


# Global instance of the default period.
default_timespan = TimeSpan()


class Sensor:
    """
    The Sensor object is used to define the sensor and the sensor's value
    range in a query.
    The Sensor object is not directly called, but created through functions
    named after the respective sensor.
    Parameters:
    name, units : (auto-defined by functions)
    min, max : minimum and maximum allowed sensor range in units.
    """

    def __init__(self, name="NaN", units="NaN", index=-1, max=1.0):
        self.name = name
        self.units = units
        self.index = index
        self.max = max

    def __copy__(self):
        return Sensor(self.name, self.units, self.index, self.max)


def Salinity(max=1.0):
    name = "Salinity"
    units = "PSU"
    index = 0
    return Sensor(name, units, index, max)


def Temperature(max=1.0):
    name = "Temperature"
    units = "Degree Celsius"
    index = 1
    return Sensor(name, units, index, max)


def CDOM(max=1.0):
    name = "CDOM"
    units = "ug/l"
    index = 2
    return Sensor(name, units, index, max)


def Chlorophyll(max=1.0):
    name = "Chlorophyll"
    units = "arb. unit"
    index = 3
    return Sensor(name, units, index, max)


def DO(max=1.0):
    name = "DO"
    units = "umol"
    index = 4
    return Sensor(name, units, index, max)


def DOSat(max=1.0):
    name = "DOSat"
    units = "percent"
    index = 5
    return Sensor(name, units, index, max)


def DO_Anomaly(max=1.0):
    name = "DO_Anomaly"
    units = "umol"
    index = 6
    return Sensor(name, units, index, max)
