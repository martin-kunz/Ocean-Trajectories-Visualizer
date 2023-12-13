import pandas as pd
import datetime
import math
import numpy as np
from multiprocessing import Pool


def compare(traj1, traj2, threshhold=15):
    traj1 = traj1.droplevel(0)
    traj2 = traj2.droplevel(0)
    shared_timestamps = traj1.index.intersection(traj2.index)

    if len(shared_timestamps) < 50:
        return False

    distances = list()
    for timestamp in shared_timestamps:
        t1 = traj1.query(f"time == '{str(timestamp)}'")
        t2 = traj2.query(f"time == '{str(timestamp)}'")
        distances.append(distance(t1.head(1).latitude, t1.head(1).longitude, t2.head(1).latitude, t2.head(1).longitude))

    # this is probably fine, as there can be no negative distance to skew this value
    avg_distance = sum(distances) / len(distances)

    if avg_distance > threshhold:
        return False

    return True


# this is stolen code which determines the distance (in km) between two geocoordinates
def distance(lat1, lon1, lat2, lon2):
    earthRadiusKm = 6371

    dLat = degtorad(lat2-lat1)
    dLon = degtorad(lon2-lon1)

    lat1 = degtorad(lat1)
    lat2 = degtorad(lat2)

    a = np.sin(dLat/2) * np.sin(dLat/2) + \
        np.sin(dLon/2) * np.sin(dLon/2) * \
        np.cos(lat1) * np.cos(lat2)
    c = 2 * math.atan2(np.sqrt(a), np.sqrt(1-a))
    return earthRadiusKm * c


def degtorad(degrees):
    return degrees * np.pi / 180


def calc_mean(group):
    return pd.Series({"longitude": group["longitude"].mean(), "latitude": group["latitude"].mean()})


def cluster(dfs):
    clustered_trajectory = pd.concat(dfs)
    return clustered_trajectory.groupby("time").apply(calc_mean)


def newlabel(labels):
    rer = ""
    for label in labels:
        rer += str(label)
    return rer


path_trajectories_db = r"../../data/trajectories.parquet"

df = pd.read_parquet(path_trajectories_db)

labels = list()

for label in df.index.get_level_values("label").drop_duplicates():
    labels.append(label)


matches = list()
i = 0

while i < len(labels)-1:
    matches.append([labels[i]])
    j = i+1
    while j < len(labels):
        if compare(df.query(f"label == {labels[i]}"), df.query(f"label == {labels[j]}")):
            matches[i].append(labels[j])
            labels.pop(j)
            j -= 1
        j += 1
    print(f"{(i/len(labels))*100}% done")
    i += 1

new_trajectories = []

for to_cluster in matches:
    trajectories = []
    for label in to_cluster:
        trajectories.append(df.query(f"label == {label}"))
    clustered = cluster(trajectories)
    clustered['label'] = newlabel(to_cluster)
    clustered['weight'] = len(to_cluster)
    clustered = clustered.reset_index().set_index(['label', 'time']).sort_index()
    new_trajectories.append(clustered)

pd.concat(new_trajectories).to_parquet('../data/clustered.parquet', engine='pyarrow')
