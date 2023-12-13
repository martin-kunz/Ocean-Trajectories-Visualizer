from globals import *


class MapInterface:
    def __init__(self, db):
        self.db = db

        # Compatability functionality with database.py, Maps String to Function that can creates Sensor Object for querries
        self.sensor_map = {
            "Salinity": Salinity,
            "Temperature": Temperature,
            "CDOM": CDOM,
            "Chlorophyll": Chlorophyll,
            "DO": DO,
            "DOSat": DOSat,
            "DO_Anomaly": DO_Anomaly,
        }

        # Caching
        # tree cache keys = tuple(sensor, start_time, end_time, sensor_dist), values = tree reference
        self.tree_cache = dict()
        self.layer9 = []
        self.layer8 = []
        self.layer7 = []
        self.layer6 = []

        # Maps map-zoom-level to tree level cells
        self.mapzoom2treezoom = {
            18: 9,
            17: 9,
            16: 9,
            15: 8,
            14: 8,
            13: 7,
            12: 7,
            11: 6,
            10: 6,
            9: 6,
            8: 6,
            7: 6,
        }

    def compute_current_tree(
        self,
        sensor: str = "Salinity",
        sensor_threshold: int = 1,
        start_time=datetime.datetime(2013, 6, 1),
        end_time=datetime.datetime(2013, 6, 30),
        dist_threshold: int = 1,
    ):
        """
        Generate the current tree that supplies heatmap data and set it to self.tree
        Also returns the distribution of contradictions over time
        :param sensor: Type of Sensor, must be a valid sensor name from data/sensor_metadata.csv, e.g. 'Salinity'
        :param sensor_threshold: Sensor value threshold for contradictions
        :param start_time: Start time for time interval of interest
        :param end_time: End time for time interval of interest
        :param dist_threshold: Max spatial distance of contradictions
        """
        # update database
        self.db.spatial_range_update(dist_threshold)
        self.db.sensor_update(sensor=self.sensor_map[sensor](sensor_threshold))

        # load from cache if possible
        if (
            sensor,
            sensor_threshold,
            start_time,
            end_time,
            dist_threshold,
        ) in self.tree_cache:
            (
                self.layer9,
                self.layer8,
                self.layer7,
                self.layer6,
                contradiction_distribution,
            ) = self.tree_cache[(sensor, sensor_threshold, start_time, end_time, dist_threshold)]
            return contradiction_distribution
        # query
        contradict_data = self.db.query(
            timespan=TimeSpan(start_time, end_time),
            sensor=self.sensor_map[sensor](),
            contradictions=True,
        )
        # Layer 9
        contradict_data.treecode = contradict_data.treecode.apply(lambda x: x[0 : 3 * 9] if (len(x) > 3 * 9) else x)
        self.layer9 = contradict_data.groupby("treecode").size().to_frame().rename(columns={0: "count"}).reset_index()
        self.layer9["bounds"] = self.layer9.treecode.map(self.db.rdict)
        # Layer 8
        self.layer9.treecode = self.layer9.treecode.apply(lambda x: x[0 : 3 * 8] if (len(x) > 3 * 8) else x)
        self.layer8 = self.layer9.groupby("treecode")["count"].sum().to_frame().rename(columns={0: "count"}).reset_index()
        self.layer8["bounds"] = self.layer8.treecode.map(self.db.rdict)
        # Layer 7
        self.layer8.treecode = self.layer8.treecode.apply(lambda x: x[0 : 3 * 7] if (len(x) > 3 * 7) else x)
        self.layer7 = self.layer8.groupby("treecode")["count"].sum().to_frame().rename(columns={0: "count"}).reset_index()
        self.layer7["bounds"] = self.layer7.treecode.map(self.db.rdict)
        # Layer 6
        self.layer7.treecode = self.layer7.treecode.apply(lambda x: x[0 : 3 * 6] if (len(x) > 3 * 6) else x)
        self.layer6 = self.layer7.groupby("treecode")["count"].sum().to_frame().rename(columns={0: "count"}).reset_index()
        self.layer6["bounds"] = self.layer6.treecode.map(self.db.rdict)
        # remove unneccessary data
        self.layer9 = self.layer9.drop(["treecode"], axis=1)
        self.layer8 = self.layer8.drop(["treecode"], axis=1)
        self.layer7 = self.layer7.drop(["treecode"], axis=1)
        self.layer6 = self.layer6.drop(["treecode"], axis=1)

        # time distribution of contradictions
        contradict_data = contradict_data.reset_index()
        contradiction_distribution = contradict_data.groupby("time").size()

        # cache
        self.tree_cache[(sensor, sensor_threshold, start_time, end_time, dist_threshold)] = (
            self.layer9.copy(),
            self.layer8.copy(),
            self.layer7.copy(),
            self.layer6.copy(),
            contradiction_distribution,
        )
        return contradiction_distribution

    def get_rects_and_heat(self, zoom_level=18):
        """
        Gets the current zoom level of the map and returns a list of tuples (boundary, heat)
        """
        layer = self.mapzoom2treezoom[zoom_level]
        if layer == 6:
            return self.layer6[["bounds", "count"]].values, self.layer6["count"].max()
        if layer == 7:
            return self.layer7[["bounds", "count"]].values, self.layer7["count"].max()
        if layer == 8:
            return self.layer8[["bounds", "count"]].values, self.layer8["count"].max()
        if layer == 9:
            return self.layer9[["bounds", "count"]].values, self.layer9["count"].max()

        return layer
