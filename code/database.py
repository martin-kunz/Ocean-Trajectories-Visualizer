from copy import copy
import time
import pandas
import numpy
from globals import *


def getstring(day, hour, label):
    """
    Constructs a formatted string based on the provided day, hour, and label.

    @param day: The day component of the date. Expected to be an integer or a value that can be converted to an integer.
    @param hour: The hour component of the time. Expected to be an integer or a value that can be converted to an integer.
    @param label: A label or identifier, expected to be a string.
    @return: A string formatted as 'DDHHlabel', where 'DD' is a zero-padded day, 'HH' is a zero-padded hour, and 'label' is the provided label.
    """
    return f"{str(day).zfill(2)}{str(hour).zfill(2)}{label}"


def getlabelids():
    """
    Reads a parquet file containing timeline data, adds a new 'id' column by combining time and label information,
    and then saves the modified dataframe back to a parquet file.

    @return: None. This function performs operations on a dataframe and saves the result, but does not return any value.
    """
    tlr = pandas.read_parquet(f"{path_timeline_ranged_db}")
    tlr["id"] = tlr.apply(lambda x: x.time.strftime("%d%H") + str(x.label), axis=1)
    print(tlr)
    tlr.to_parquet(path_timeline_ranged_db)


def getddict():
    """
    Creates a dictionary (ddict) mapping sensor labels to various attributes like positions, sensors, and distances.
    It reads data from parquet files, computes distances and aggregates sensor data.

    @return: None. This function is used for side effects (like creating or modifying a global variable) rather than returning a value.
    """
    neighbour_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neighbours")
    result_path = os.path.join(neighbour_path, f"{max_distance_threshold}km_distance")
    sensors = pandas.read_parquet(f"{path_sensors_db}")
    timeline = pandas.read_parquet(f"{path_time_db}")
    ddict = {}
    global_index = 0
    t10 = time.time()
    max_sensors_threshold = [0, 0, 0, 0, 0, 0, 0]
    min_sensor_thresholds = [0, 0, 0, 0, 0, 0, 0]
    threshold_count = 0
    for day in range(1, 31):
        for hour in range(0, 24):
            prefix = f"{str(day).zfill(2)}{str(hour).zfill(2)}"
            print(prefix)
            timenow = datetime.datetime(2013, 6, day, hour)
            with open(os.path.join(result_path, f"{day}_{hour}.csv"), "r") as f:
                for line in f:
                    label_list = line.strip().rstrip(",").split(",")
                    key_label = numpy.int32(label_list[0])
                    key_pos = timeline.loc[(timenow, key_label)].values[0]
                    key_sensors = sensors.loc[key_label].values[3:11]
                    key_value = []
                    if len(label_list) <= 1:
                        continue
                    for i in range(1, len(label_list)):
                        current_label = int(label_list[i])
                        current_pos = timeline.loc[(timenow, current_label)].values[0]
                        current_sensors = sensors.loc[current_label].values[3:11]
                        distance = numpy.float32(distance_wgs(key_pos[0], key_pos[1], current_pos[0], current_pos[1]))
                        sensor_difference = numpy.zeros([len(current_sensors)])
                        for j in range(0, len(current_sensors)):
                            if numpy.isnan(key_sensors[j]) or numpy.isnan(current_sensors[j]):
                                sensor_difference[j] = 0
                            else:
                                diff = abs(key_sensors[j] - current_sensors[j])
                                sensor_difference[j] = diff
                                threshold_count += 1
                                min_sensor_thresholds[j] += diff
                                if diff > max_sensors_threshold[j]:
                                    max_sensors_threshold[j] = diff

                        key_value.append((distance, sensor_difference))

                    key_value = sorted(key_value, key=lambda tup: tup[0])
                    # Key values sind sortiert - Idee:
                    # 1) wir berechnen die max map pro key
                    # 2) Jeder Key bekommt range [key,next_key)
                    # 2) Wir werfen keys raus, deren max map sich nicht vom vorherigen key unterscheidet
                    # Wir fügen in eine DB ein:
                    #   Index: Time, Label, key, nextkey
                    #   Columns: Original time,label,lon,lat + 7 maxvals (precomputed s_dict from below function)
                    # Corner case: No neighbors: don't save aka, we don't need them
                    # Corner case, lets say we have vals 0.46, 0.83, how to fully define 0-1?
                    # [0.00, 0.46) -> no threshold -> no errors -> does not need to appear in error list
                    # [0.46, 0.83) -> 0.46 max values
                    # [0.83, 1.00) -> 0.83 max values
                    for i in range(1, len(key_value)):
                        key_value[i] = (key_value[i][0], numpy.maximum(key_value[i - 1][1], key_value[i][1]))
                    rmax = numpy.float32(max_distance_threshold + 0.0001)  # in km
                    for i in reversed(range(1, len(key_value))):
                        if numpy.array_equal(key_value[i][1], key_value[i - 1][1]):
                            continue
                        ddict[global_index] = [
                            timenow,
                            key_label,
                            key_pos[0],
                            key_pos[1],
                            key_value[i][0],
                            rmax,
                            numpy.float32(key_value[i][1][0]),
                            numpy.float32(key_value[i][1][1]),
                            numpy.float32(key_value[i][1][2]),
                            numpy.float32(key_value[i][1][3]),
                            numpy.float32(key_value[i][1][4]),
                            numpy.float32(key_value[i][1][5]),
                            numpy.float32(key_value[i][1][6]),
                        ]
                        global_index += 1
                        rmax = key_value[i][0]
                    # last value
                    ddict[global_index] = [timenow, key_label, key_pos[0], key_pos[1], key_value[0][0], rmax]
                    ddict[global_index] = [
                        timenow,
                        key_label,
                        key_pos[0],
                        key_pos[1],
                        key_value[0][0],
                        rmax,
                        numpy.float32(key_value[0][1][0]),
                        numpy.float32(key_value[0][1][1]),
                        numpy.float32(key_value[0][1][2]),
                        numpy.float32(key_value[0][1][3]),
                        numpy.float32(key_value[0][1][4]),
                        numpy.float32(key_value[0][1][5]),
                        numpy.float32(key_value[0][1][6]),
                    ]
                    global_index += 1
    timeline_new = pandas.DataFrame.from_dict(
        ddict, orient="index", columns=["time", "label", "longitude", "latitude", "rmin", "rmax", "s0", "s1", "s2", "s3", "s4", "s5", "s6"]
    )
    for i in range(0, len(min_sensor_thresholds)):
        min_sensor_thresholds[i] /= threshold_count
        min_sensor_thresholds[i] /= 2
    print(f"Min: {min_sensor_thresholds}")
    print(f"Max: {max_sensors_threshold}")
    t12 = time.time()
    print(f"Nearest neighbours loaded in:{t12-t10:.02f}s")
    timeline_new.to_parquet(os.path.join(neighbour_path, "timelinenew.parquet"))
    return


class Database:

    def __init__(self):
        """
        Constructor for the Database class. Initializes the class by loading various data from parquet and CSV files into pandas DataFrames.
        It also sets up some threshold values and prepares data structures for further operations.

        @return: None. This is a constructor method for initializing a new instance of the Database class.
        """
        self.sensors = pandas.read_parquet(path_sensors_db)
        self.timeline = pandas.read_parquet(path_time_db)
        self.tlr = pandas.read_parquet(path_timeline_ranged_db)
        self.trajectories = pandas.read_parquet(path_trajectories_db)
        self.meta = pandas.read_csv(path_meta_db)
        self.clustered = pandas.read_parquet(path_clustered)
        self.rdict = pandas.read_pickle(path_range_dict)
        self.dthresh = max_distance_threshold
        self.sthresh = numpy.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        # Wie gehen wir vor?
        # Generate ddict based on csv: DDict: sensorval+distance per label
        # OnRangeUpdate->   Query ddict for all neighbors < dthresh -> get list of labels
        #                   Query list for max sthresh, update sdict
        # OnSensorUpdate/OnRangeUpdate->   isContradiction(sdict) returns dict for label, if contradictionary
        # QUERY CDICT with contradicts(label)

        # ddict -> offline
        # sdict -> on range_update(threshold)
        # cdict -> on range_update(threshold) and sensor_update(thresholds)

        # sdict size: Unique sensor values * 7 float
        # cdict size: Unique sensor values * 7 bool
        # idea: store directly inside DF
        # sdict is stored as s0-s6 in timeline_ranged (tlr)
        # Update: All got preprocessed in timeline_ranged as sdict
        # We now just need to update d and s thresh and do a dynamic query

    def query(
        self, region: Region = default_region, timespan: TimeSpan = default_timespan, sensor: Sensor = Salinity(), contradictions: bool = False
    ):
        cregion = copy(region)
        ctimespan = copy(timespan)
        sensorid = sensor.index
        if cregion.projection == "Web":
            cregion.web_to_wgs()
        results = []
        if contradictions:
            results = self.tlr.loc[
                (self.tlr.time >= ctimespan.start)
                & (self.tlr.time <= ctimespan.end)
                & (self.tlr.rmin <= self.dthresh)
                & (self.tlr.rmax > self.dthresh)
                & (self.tlr[f"s{sensorid}"] > self.sthresh[sensorid])
            ]
            results = results.iloc[:, [0, 1, 13, 14]]
        else:
            results = self.timeline.loc[ctimespan.start : ctimespan.end]

        if cregion != default_region:
            results = results[
                (results.longitude >= cregion.x_min)
                & (results.longitude < cregion.x_max)
                & (results.latitude >= cregion.y_min)
                & (results.latitude < cregion.y_max)
            ]
        return results


    def spatial_range_update(self, range: float):
        """
        Updates the spatial range threshold (dthresh) of the database.

        @param range: A float value representing the new spatial range threshold.
        @return: None. This method updates the internal state of the object but does not return any value.
        """
        self.dthresh = range
        return


    def sensor_update(self, sensor: Sensor):
        """
        Updates the sensor threshold array (sthresh) for a specific sensor index based on the provided sensor object.

        @param sensor: A 'Sensor' object which contains sensor information including index and maximum threshold value.
        @return: None. This method updates the internal state of the object but does not return any value.
        """
        idx = sensor.index
        self.sthresh[idx] = sensor.max
        return
