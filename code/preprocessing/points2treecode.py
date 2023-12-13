from globals import *
import pickle
import os
import quadTree as qt
import pandas as pd

"""
This script writes a dictionary to ./trees/allData/points2treecode.p that maps each id of format 
f"{str(day).zfill(2)}{str(hour).zfill(2)}{label}"
to its respective leaf in the tree from trees/allData/timeQuadTree.p
"""
if __name__ == "__main__":
    # resulting dict
    points2trees = dict()

    # all points
    df = pd.read_parquet(path_trajectories_db)

    # get tree
    with open(os.path.join(tree_path, "timeQuadTree.p"), "rb") as f:
        tree = pickle.load(f)

        # go through each point
        for row in df.itertuples():
            (label, time), lon, lat = row
            uid = f"{str(time.day).zfill(2)}{str(time.hour).zfill(2)}{label}"

            # get code from tree
            point = qt.Point([(time, label), (lon, lat)])
            code = tree.get_tree_code(point)

            # save to dict
            points2trees[uid] = code

    # write dict to file
    with open(os.path.join(tree_path, "points2treecode.p"), "wb") as f2:
        pickle.dump(points2trees, f2)
