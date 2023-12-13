import os
import time
import datetime
import xarray as xa
import pandas

debug = True

path_sensors_raw = r"data/obs_2013.nc"
path_bw = r"data/BW"
path_fw = r"data/FW"
prefix = r"synop_201306"
suffix = r".nc"
year = 2013
month = 6
month_days = 30

path_sensors_db = r"data/sensors.parquet"
path_meta_db = r"data/sensors_metadata.csv"
path_trajectories_db = r"data/trajectories.parquet"
path_time_db = r"data/timeline.parquet"


def preprocessing():
    """ sensors.parquet

        loaded with: df = pandas.read_parquet(path_sensors_db)
    """
    ds = xa.load_dataset(path_sensors_raw)
    df = ds.to_dataframe()
    df = df.drop(labels=["QF_sensor_1", "QF_sensor_2", "QF_sensor_3",
                 "QF_sensor_4", "QF_sensor_5", "QF_sensor_6", "QF_sensor_7"], axis=1)
    df.index = pandas.to_datetime(df.index.str.decode(encoding='ASCII'))
    df.label = df.label.str.decode(encoding='ASCII').astype(int)
    df = df.reset_index()
    df = df.set_index(df.label).drop(labels="label", axis=1)
    # set sensor name right
    dd = pandas.DataFrame(columns=['long_name', 'units'])
    for x in list(ds.keys()):
        if x.startswith("sensor"):
            dd.loc[x] = ds.data_vars.get(x).attrs
            df = df.rename(columns={x: dd.loc[x].long_name})
    dd.index.name = 'name'
    # save
    dd.to_csv(path_meta_db)
    df.to_parquet(path_sensors_db)
    if debug:
        print(dd.info())
        print(df.info())

    """ trajectories.parquet

        loaded with: df = pandas.read_parquet(path_trajectories_db)
    """
    tr = pandas.DataFrame(columns=['label', 'time', 'longitude', 'latitude'])
    tr = tr.astype(dtype={
                   'label': 'int64', 'time': 'datetime64[ns]', 'longitude': 'float32', 'latitude': 'float32'})
    count = 0
    # BW
    for day in range(1, month_days+1):
        for hour in range(0, 24):
            file_path = os.path.join(
                path_bw, f"{prefix}{day:02i}{hour:02i}{suffix}")
            bw = 0
            try:
                ds = xa.load_dataset(file_path)
                bw = ds.to_dataframe()
                count += len(bw)
            except Exception as e1:
                print(f"Problem with file {file_path}\n", e1)
                continue
            bw = bw.drop(labels=["initial_year", "travel_time"], axis=1)
            bw.label = bw.label.str.decode(encoding='ASCII').astype(int)
            bw["time"] = datetime.datetime(year, month, day, hour)
            tr = pandas.concat([tr, bw], axis=0, ignore_index=True)
    # FW
    for day in range(1, month_days+1):
        for hour in range(0, 24):
            file_path = os.path.join(
                path_fw, f"{prefix}{day:02i}{hour:02i}{suffix}")
            fw = 0
            try:
                ds = xa.load_dataset(file_path)
                fw = ds.to_dataframe()
                count += len(fw)
            except Exception as e1:
                print(f"Problem with file {file_path}\n", e1)
                continue
            fw = fw.drop(labels=["initial_year", "travel_time"], axis=1)
            fw.label = fw.label.str.decode(encoding='ASCII').astype(int)
            fw["time"] = datetime.datetime(year, month, day, hour)
            tr = pandas.concat([tr, fw], axis=0, ignore_index=True)
    # save by trajectory
    tr = tr.set_index(['label', 'time']).sort_index()
    tr.to_parquet(path_trajectories_db, engine='pyarrow')
    if debug:
        print(tr.info())
        print(f"Count:      {count}")
        print(f"Datapoints: {len(tr)}")
    # save by time
    tr = tr.reset_index().set_index(['time', 'label']).sort_index()
    tr.to_parquet(path_time_db, engine='pyarrow')
    if debug:
        print(tr.info())


if __name__ == '__main__':
    time_start = time.time()
    preprocessing()
    print(f"Data preprocessed in {time.time()-time_start}s")
