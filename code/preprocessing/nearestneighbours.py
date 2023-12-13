import os
import pickle
import time
import datetime
import quadTree as qt
from globals import *
import database


if __name__ == "__main__":
    t10 = time.time()

    # Value for neighbour distance in km
    contradiction_distance = max_distance_threshold

    db = database.Database()

    neighbour_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../neighbours")
    try:
        os.mkdir(neighbour_path)
    except FileExistsError:
        pass
    result_path = os.path.join(neighbour_path, f"{contradiction_distance}km_distance")
    try:
        os.mkdir(result_path)
    except FileExistsError:
        pass

    for day in range(1, 31):
        for hour in range(0, 24):
            print(f"{str(day).zfill(2)}/{str(hour).zfill(2)}")
            with open(os.path.join(result_path, f"{day}_{hour}.csv"), "w") as f:
                t1 = datetime.datetime(2013, 6, day, hour)
                ts = TimeSpan(t1, t1)
                timestamp_data = db.query(timespan=ts)
                timestamp_data = timestamp_data.reset_index(level=0, drop=True)
                vfunc = np.vectorize(distance_wgs)
                for row in timestamp_data.itertuples():
                    label, lon, lat = row
                    tsd = timestamp_data.drop([label])
                    within_distance_data = tsd[vfunc(lon, lat, tsd["longitude"], tsd["latitude"]) <= contradiction_distance]
                    f.write(f"{label},{','.join(within_distance_data.index.format())}\n")
    t12 = time.time()
    print(f"Benchmarked time:{t12-t10:.02f}")
