import numpy as np
from globals import Region, default_region
import os
import pandas as pd


class Point:
    """A point located at (long, lat) in 2D space.

    Each Point object may be associated with a payload object.

    """

    def __init__(self, data):
        self.long, self.lat = data[1][0], data[1][1]
        self.time = data[0][1]
        self.label = data[0][0]

    def __repr__(self):
        return f'({self.label},{self.time},({self.long},{self.lat}))'

    def __str__(self):
        return f'Particle: {self.label} at Time: {self.time} at:  {self.long}, {self.lat}: '

    def distance_to(self, other):
        try:
            other_long, other_lat = other.long, other.lat
        except AttributeError:
            other_long, other_lat = other
        return np.hypot(self.long - other_long, self.lat - other_lat)

    def get_time(self):
        return self.time

    def get_label(self):
        return self.label

    def get_coordinates(self):
        return self.long, self.lat


class QuadTree:
    """A class implementing a quadtree."""

    def __init__(self, boundary, max_points=4, depth=0, max_depth=20, parent=None, code=""):
        """Initialize this node of the quadtree.

        boundary is a Rect object defining the region from which points are
        placed into this node; max_points is the maximum number of points the
        node can hold before it must divide (branch into four more nodes);
        depth keeps track of how deep into the quadtree this node lies.
        max_depth defines the maximal depth of the tree, if this depth is reached tree cells are no longer divided and points are inserted in the lowest cell, in this case surpassing max_points is allowed
        parent refers to the super-tree, this can be used for any bottom-up approach and should be None for the top-level
        code represents a sequence of elements from {'nw','ne','sw','se'} seperated by '.' that can be used to quickly access a subtree
        points are only stored in leaf nodes
        """

        self.boundary = boundary
        self.max_points = max_points
        self.points = []
        self.depth = depth
        self.parent = parent

        # A flag to indicate whether this node has divided (branched) or not.
        self.divided = False

        # counter for contradictions
        self.count = 0

        self.max_depth = max_depth

        self.code = code

    def __str__(self):
        """Return a string representation of this node, suitably formatted."""
        sp = ' ' * self.depth * 2
        s = str(self.boundary) + '\n'
        s += sp + ', '.join(str(point) for point in self.points)
        if not self.divided:
            return s
        return s + '\n' + '\n'.join([
            sp + 'nw: ' + str(self.nw), sp + 'ne: ' + str(self.ne),
            sp + 'se: ' + str(self.se), sp + 'sw: ' + str(self.sw)])

    def divide(self):
        """Divide (branch) this node by spawning four children nodes."""
        w, h = self.boundary.w / 2, self.boundary.h / 2

        horizontal_branching_point = self.boundary.x_min + w
        vertical_branching_point = self.boundary.y_min + h

        self.nw = QuadTree(Region(self.boundary.x_min,
                                  horizontal_branching_point,
                                  vertical_branching_point,
                                  self.boundary.y_max),
                           self.max_points, self.depth + 1, parent=self, max_depth=self.max_depth, code=self.code+".nw")

        self.ne = QuadTree(Region(horizontal_branching_point,
                                  self.boundary.x_max,
                                  vertical_branching_point,
                                  self.boundary.y_max),
                           self.max_points, self.depth + 1, parent=self, max_depth=self.max_depth, code=self.code+".ne")

        self.se = QuadTree(Region(horizontal_branching_point,
                                  self.boundary.x_max,
                                  self.boundary.y_min,
                                  vertical_branching_point),
                           self.max_points, self.depth + 1, parent=self, max_depth=self.max_depth, code=self.code+".se")

        self.sw = QuadTree(Region(self.boundary.x_min,
                                  horizontal_branching_point,
                                  self.boundary.y_min,
                                  vertical_branching_point),
                           self.max_points, self.depth + 1, parent=self, max_depth=self.max_depth, code=self.code+".sw")

        # points should only be stored in leaf nodes
        for point in self.points:
            self.ne.insert(point)
            self.nw.insert(point)
            self.se.insert(point)
            self.sw.insert(point)
        self.points = []

        self.divided = True

    def insert(self, point):
        """Try to insert Point point into this QuadTree."""

        if not self.boundary.contains(point):
            # The point does not lie inside boundary: bail.
            return False

        # insert point only if this node is a leaf and if it can either hold new points or it is at maximal allowed depth
        if not self.divided:
            if len(self.points) < self.max_points or self.depth == self.max_depth:
                self.points.append(point)
                return True
            # No room and not at max_depth: divide if necessary
            else:
                self.divide()

        # try subtrees if tree is divided
        return (self.ne.insert(point) or
                self.nw.insert(point) or
                self.se.insert(point) or
                self.sw.insert(point))

    def query(self, boundary, found_points):
        """Find the points in the quadtree that lie within boundary."""

        if not self.boundary.intersects(boundary):
            # If the domain of this node does not intersect the
            # search region, we don't need to look in it for points.
            return False

        # Search this node's points to see if they lie within boundary ...
        for point in self.points:
            if boundary.contains(point):
                found_points.append(point)
        # ... and if this node has children, search them too.
        if self.divided:
            self.nw.query(boundary, found_points)
            self.ne.query(boundary, found_points)
            self.se.query(boundary, found_points)
            self.sw.query(boundary, found_points)
        return True

    def query_circle(self, boundary, centre, radius, found_points):
        """Find the points in the quadtree that lie within radius of centre.

        boundary is a Rect object (a square) that bounds the search circle.
        There is no need to call this method directly: use query_radius.

        """

        if not self.boundary.intersects(boundary):
            # If the domain of this node does not intersect the
            # search region, we don't need to look in it for points.
            return False

        # Search this node's points to see if they lie within boundary
        # and also lie within a circle of given radius around the centre point.
        for point in self.points:
            if (boundary.contains(point) and
                    point.distance_to(centre) <= radius):
                found_points.append(point)

        # Recurse the search into this node's children.
        if self.divided:
            self.nw.query_circle(boundary, centre, radius, found_points)
            self.ne.query_circle(boundary, centre, radius, found_points)
            self.se.query_circle(boundary, centre, radius, found_points)
            self.sw.query_circle(boundary, centre, radius, found_points)
        return True

    def query_radius(self, centre, radius, found_points):
        """Find the points in the quadtree that lie within radius of centre."""

        # First find the square that bounds the search circle as a Rect object.
        cx, cy = centre[0], centre[1]
        boundary = Region(cx - radius, cx + radius, cy - radius, cy + radius)
        return self.query_circle(boundary, centre, radius, found_points)

    def __len__(self):
        """Return the number of points in the quadtree."""

        npoints = len(self.points)
        if self.divided:
            npoints += len(self.nw) + len(self.ne) + len(self.se) + len(self.sw)
        return npoints

    def draw(self, ax):
        """Draw a representation of the quadtree on Matplotlib Axes ax."""

        self.boundary.draw(ax)
        if self.divided:
            self.nw.draw(ax)
            self.ne.draw(ax)
            self.se.draw(ax)
            self.sw.draw(ax)

    def increase_count(self, n=1):
        """
        Increase this node's count and propagate the count upwards the tree
        :param n indicates the amount the count should be increased, default is 1
        """
        self.count += n
        if self.depth > 0:
            self.parent.increase_count(n)
        return self.count

    def reset_count(self):
        """Reset the count of this tree and each child"""
        self.count = 0
        if self.divided:
            self.nw.reset_count()
            self.ne.reset_count()
            self.sw.reset_count()
            self.se.reset_count()

    def get_subtree_from_code(self, code):
        """
        Get to a subtree of this tree by using a String representation of subtrees
        :param code: Sequence of *['.nw','.ne','.sw','.sw'], that will be used to get the subtree, other strings will return a None instance
        :return: Tree or None
        """
        try:
            tree = eval("self"+code)
            return tree
        except Exception:
            return None

    def get_tree_code(self, point):
        """
        Recursively get the code of the leaf node containing point
        :param point: Point that tree is searched for
        :return: Code as a String of the tree that can be used in get_subtree_from_code to later get the same tree
        """
        if self.divided:
            if self.nw.boundary.contains(point):
                return self.nw.get_tree_code(point)
            elif self.ne.boundary.contains(point):
                return self.ne.get_tree_code(point)
            elif self.sw.boundary.contains(point):
                return self.sw.get_tree_code(point)
            elif self.se.boundary.contains(point):
                return self.se.get_tree_code(point)
        else:
            return self.code

    def get_tree_cell(self, point):
        """
        Recursively get the leaf node containing point
        :param point: Point that tree is searched for
        :return: Tree cell that contains the point
        """
        if self.divided:
            if self.nw.boundary.contains(point):
                return self.nw.get_tree_code(point)
            elif self.ne.boundary.contains(point):
                return self.ne.get_tree_code(point)
            elif self.sw.boundary.contains(point):
                return self.sw.get_tree_code(point)
            elif self.se.boundary.contains(point):
                return self.se.get_tree_code(point)
        else:
            return self


class TimeQuadTree(QuadTree):
    """A class implementing a quadtree that also records the time interval of its points and allows to query for timestamps"""

    def __init__(self, boundary, max_points=4, depth=0, max_depth=20, parent=None, code=""):
        """Constructor is the same as for QuadTrees but also creates the fields for the time interval stored in this (sub)tree """

        self.minTime = None
        self.maxTime = None
        super().__init__(boundary, max_points, depth, max_depth, parent, code)

    def __str__(self):
        """Return a string representation of this node, suitably formatted."""
        sp = ' ' * self.depth * 2
        s = str(self.boundary) + f"{str(self.minTime)}-{str(self.maxTime)}" + '\n'
        s += sp + ', '.join(str(point) for point in self.points)
        if not self.divided:
            return s
        return s + '\n' + '\n'.join([
            sp + 'nw: ' + str(self.nw), sp + 'ne: ' + str(self.ne),
            sp + 'se: ' + str(self.se), sp + 'sw: ' + str(self.sw)])

    def divide(self):
        """Divide (branch) this node by spawning four children nodes."""
        w, h = self.boundary.w / 2, self.boundary.h / 2

        horizontal_branching_point = self.boundary.x_min + w
        vertical_branching_point = self.boundary.y_min + h

        self.nw = TimeQuadTree(Region(self.boundary.x_min,
                                      horizontal_branching_point,
                                      vertical_branching_point,
                                      self.boundary.y_max),
                               self.max_points, self.depth + 1, parent=self, max_depth=self.max_depth, code=self.code+".nw")

        self.ne = TimeQuadTree(Region(horizontal_branching_point,
                                      self.boundary.x_max,
                                      vertical_branching_point,
                                      self.boundary.y_max),
                               self.max_points, self.depth + 1, parent=self, max_depth=self.max_depth, code=self.code+".ne")

        self.se = TimeQuadTree(Region(horizontal_branching_point,
                                      self.boundary.x_max,
                                      self.boundary.y_min,
                                      vertical_branching_point),
                               self.max_points, self.depth + 1, parent=self, max_depth=self.max_depth, code=self.code+".se")

        self.sw = TimeQuadTree(Region(self.boundary.x_min,
                                      horizontal_branching_point,
                                      self.boundary.y_min,
                                      vertical_branching_point),
                               self.max_points, self.depth + 1, parent=self, max_depth=self.max_depth, code=self.code+".sw")

        # points should only be stored in leaf nodes
        for point in self.points:
            self.ne.insert(point)
            self.nw.insert(point)
            self.se.insert(point)
            self.sw.insert(point)
        self.points = []

        self.divided = True

    def insert(self, point):
        """
        Inserts the Point point like in QuadTree.insert() but also updates the time Interval of this (sub)Tree
        As QuadTree.insert() is recursive the time interval of a parent tree always includes the intervals of its children
        """

        if super().insert(point):  # this is True if the insertion was successful
            point_time = point.time
            if self.minTime is None or point_time < self.minTime:
                self.minTime = point_time
            if self.maxTime is None or point_time > self.maxTime:
                self.maxTime = point_time
            return True
        else:
            return False

    def checkTimeConstraints(self, timeMin, timeMax):
        """Check whether a queried time interval satisfies certain criteria"""

        if timeMin > timeMax:
            # Min bigger than Max Value
            return False
        if self.minTime is None or self.maxTime is None:
            # Queried node has no points
            return False
        if timeMin > self.maxTime or timeMax < self.minTime:
            # Queried time interval lies outside this nodes time interval
            return False

        return True

    def time_query(self, boundary, found_points, timeMin, timeMax):
        """Find the points in the quadtree that lie within boundary and a time interval."""

        if not self.checkTimeConstraints(timeMin, timeMax):
            return False

        if not self.boundary.intersects(boundary):
            # If the domain of this node does not intersect the
            # search region, we don't need to look in it for points.
            return False

        # Search this node's points to see if they lie within boundary and queried time interval...
        for point in self.points:
            if boundary.contains(point) and timeMin <= point.time <= timeMax:
                found_points.append(point)
        # ... and if this node has children, search them too.
        if self.divided:
            self.nw.time_query(boundary, found_points, timeMin, timeMax)
            self.ne.time_query(boundary, found_points, timeMin, timeMax)
            self.se.time_query(boundary, found_points, timeMin, timeMax)
            self.sw.time_query(boundary, found_points, timeMin, timeMax)
        return True

    def time_query_circle(self, boundary, centre, radius, found_points, timeMin, timeMax):
        """Find the points in the quadtree that lie within radius of centre and inside a given time interval.

        boundary is a Rect object (a square) that bounds the search circle.
        There is no need to call this method directly: use query_radius.
        """

        if not self.checkTimeConstraints(timeMin, timeMax):
            return False

        if not self.boundary.intersects(boundary):
            # If the domain of this node does not intersect the
            # search region, we don't need to look in it for points.
            return False

        # Search this node's points to see if they lie within boundary,
        # within the queried time interval
        # and also lie within a circle of given radius around the centre point.
        for point in self.points:
            if boundary.contains(point) and point.distance_to(centre) <= radius and timeMin <= point.time <= timeMax:
                found_points.append(point)

        # Recurse the search into this node's children.
        if self.divided:
            self.nw.time_query_circle(boundary, centre, radius, found_points, timeMin, timeMax)
            self.ne.time_query_circle(boundary, centre, radius, found_points, timeMin, timeMax)
            self.se.time_query_circle(boundary, centre, radius, found_points, timeMin, timeMax)
            self.sw.time_query_circle(boundary, centre, radius, found_points, timeMin, timeMax)
        return True

    def time_query_radius(self, centre, radius, found_points, timeMin, timeMax):
        """Find the points in the quadtree that lie within radius of centre and within the queried time interval."""
        cx, cy = centre[0], centre[1]

        # First find the square that bounds the search circle as a Rect object.
        boundary = Region(cx - radius, cx + radius, cy - radius, cy + radius)
        return self.time_query_circle(boundary, centre, radius, found_points, timeMin, timeMax)
