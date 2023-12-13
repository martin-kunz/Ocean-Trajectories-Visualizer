import pandas as pd
from globals import *


class Interface:
    """Dummy for Frontend-Backend Interface"""

    def __init__(self, db):
        self.db = db
        # Sensor data
        self.sensor_lookup = db.sensors
        # Get trajectory data from database and preprocess it
        self.tr = db.trajectories.reset_index()
        self.tr["day"] = self.tr["time"].apply(lambda x: x.day)
        self.tr = self.tr.sort_values(by="time")

    def get_graph_data(
        self,
        sensor: str,
        fov=Region(7.88, 7.92, 54.095, 54.105),
        start_time=pd.Timestamp(year=2013, month=6, day=1),
        end_time=pd.Timestamp(year=2013, month=6, day=30, hour=23, minute=59),
        unique=True,
    ):
        """
        Queries sensor values in given fov and time interval and also returns corresponding timestamps
        :param sensor: Type of Sensor must be a valid sensor name from data/sensor_metadata.csv, e.g. 'Salinity'
        :param fov: Area of interest, default is qt.Rect(7.9, 54.1, 0.02, 0.005), Increasing size increases runtime greatly
        :param start_time: Start time for time interval of interest, default is 2013.06.01 0:0
        :param end_time: End time for time interval of interest, default is 2013.06.30 23:59
        :param unique: Whether only one point per trajectory should be included in histogram
        :return: Pandas dataFrame filtered according to parameter of this function and with appended sensor values to each row
        """

        filtered_data = self.tr[
            (self.tr.longitude >= fov.x_min)
            & (self.tr.longitude < fov.x_max)
            & (self.tr.latitude >= fov.y_min)
            & (self.tr.longitude < fov.y_max)
            & (self.tr.time >= start_time)
            & (self.tr.time < end_time)
        ]

        sensor_vals = self.sensor_lookup[sensor]
        data_with_sensor = pd.merge(filtered_data, sensor_vals, how="left", left_on="label", right_on="label")

        return data_with_sensor
