import pickle
import sys
import os
import quadTree as qt
import pandas as pd
from globals import *

"""
This script builds a timeQuadTree for all data and a single timeQuadTree for each day in June 2013 from the observation data.
Trees are serialised in the './trees/[name]/' directory.
The timeQuadTree is saved to the file './trees/[name]timeQuadTree.p'
The Daily Trees are saved as './trees/[name]/day_[day_of_month].p'

Accepts the path to a dataset in parquet format as an optional first parameter and builds the trees from this dataset.
If no parameter is supplied default is '/data/trajectories.parquet' and [name] is "allData"

If a second parameter is presented to the script it is used as [name].
Otherwise [name] is 'unnamedTree'
"""
if __name__ == '__main__':

    # Get name
    if len(sys.argv) > 2:
        name = sys.argv[2]
    else:
        name = "unnamedTree"

    # Load dataset
    if len(sys.argv) > 1:
        path = sys.argv[1]
        data = pd.read_parquet(path)
    else:
        data_path = os.path.join(os.path.split(os.path.dirname(os.path.abspath(__file__)))
                                 [0], 'data/trajectories.parquet')
        data = pd.read_parquet(data_path)
        name = "allData"

    # get output path
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'trees/{name}')

    targetArea = default_region


    """ 
    The ranges in lat/long values are very small (53.xx-54.xx in lat)
    Dividing a quadtree cell requires the division of this range
    Therefore if the max number of points in a cell is too small this division at some point will lead to a loss of floating point precision
    This leads to possible errors for inserting points in a quadtree
    Empirically proven is that max_points = 4 leads to such errors, max_points = 10 works fine
    """
    # single tree
    tree = qt.TimeQuadTree(targetArea, max_points=20)

    # daily trees
    d_trees = [qt.TimeQuadTree(targetArea, max_points=20) for i in range(30)]

    # Insert each datapoint from the dataset
    for row in data.iterrows():
        p = qt.Point(row)

        if not tree.insert(p):
            raise Exception(
                f"Can't insert Point {str(p)} into Time Quad Tree maybe increase maximal allowed points in single quad tree cell")
        if not d_trees[p.time.day-1].insert(p):  # array 0-indexed, days start at 1
            raise Exception(
                f"Can't insert Point {str(p)} into Time Quad Tree maybe increase maximal allowed points in single quad tree cell")

    # Save trees to files
    try:
        os.mkdir(output_path)
        os.mkdir(os.path.join(output_path, 'daily'))
    except FileExistsError:  # we don't care if directories already exist
        pass
    with open(os.path.join(output_path, 'timeQuadTree.p'), 'wb') as f:
        pickle.dump(tree, f)

    for index, tree in enumerate(d_trees):
        day_index = index+1  # array 0-indexed, days start at 1
        with open(os.path.join(output_path, f'daily/day_{day_index}.p'), 'wb') as f:
            pickle.dump(tree, f)
