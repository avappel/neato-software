# Analyzes lidar data to obtain information about the environs.

from __future__ import division

from pyhull.convex_hull import ConvexHull

import math
import sys

from programs import log

import utilities

# Represents a line.
class Line:
  hull = None

  @staticmethod
  # Find intersection of two lines.
  def find_intersection(line1, line2):
    if line1.slope[0] == 0:
      x = Line.hull[line1.index][0]
      y = line2.evaluate(x)
    elif line2.slope[0] == 0:
      x = Line.hull[line2.index][0]
      y = line1.evaluate(x)
    else:
      line1_slope = line1.slope[1] / line1.slope[0]
      line2_slope = line2.slope[1] / line2.slope[0]
      x = (line2.intercept - line1.intercept) / (line1_slope - line2_slope)
      y = line1.evaluate(x)

    return (x, y)

  @staticmethod
  # Find angle between two lines.
  def find_angle_between(line1, line2):
    return abs(line2.angle - line1.angle)

  def __init__(self, p1, p2, hullpoint_index):
    self.slope = (p2[0] - p1[0], p2[1] - p1[1])
    self.index = hullpoint_index
    log.debug("Line slope, index: %s, %d." % (self.slope, self.index))

  # Find intercept.
  @property
  def intercept(self):
    hullpoint = Line.hull[self.index]
    slope = self.slope[1] / self.slope[0]
    return hullpoint[1] - slope * hullpoint[0]

  # Find angle.
  @property
  def angle(self):
    if self.slope[0] == 0:
      if self.slope[1] > 0:
        return math.pi / 2
      elif self.slope[1] < 0:
        return -math.pi / 2

    return math.atan(self.slope[1] / self.slope[0])

  # Evaluate an x value.
  def evaluate(self, x):
    slope = self.slope[1] / self.slope[0]
    return  slope * x + self.intercept

  # Makes the slope orthogonal.
  def orthogonal(self, line):
    self.slope = [-line.slope[1], line.slope[0]]

# Calculate convex hull.
def convex_hull(scan):
  hull = ConvexHull(scan)

  # Draw it on the canvas.
  points = []
  hull.vertices.pop(len(hull.vertices) // 2)
  for vertex in hull.vertices:
    points.append(scan[vertex[0]])
  points.append(scan[hull.vertices[-1][1]])

  log.debug("Convex hull: %s." % (points))
  return points

# Calculates the dimensions of a rectangle defined by 4 lines, where l1 || to l2 and
# l3 || l4
def rectangle_dimensions(l1, l2, l3, l4):
  p1 = Line.find_intersection(l1, l3)
  p2 = Line.find_intersection(l2, l4)
  p3 = Line.find_intersection(l1, l4)
  p4 = Line.find_intersection(l2, l3)
  log.debug("Rectangle points: %s, %s, %s, %s." % (p1, p2, p3, p4))

  # p1 and p2 are diagonally opposite.
  w = utilities.distance(p1, p3)
  l = utilities.distance(p2, p3)
  log.debug("Length, Width: %f, %f." % (l, w))

  return ((p1, p2, p3, p4), (w, l))

# Calculate OMBB points. Takes a set of points as its input.
def ombb(points):
  hull = convex_hull(points)
  Line.hull = hull

  # Find extreme points.
  x_max = -sys.maxint
  x_min = sys.maxint
  y_max = -sys.maxint
  y_min = sys.maxint

  top_point = None
  bottom_point = None
  left_point = None
  right_point = None

  for i in range(0, len(hull)):
    point = hull[i]

    if point[0] > x_max:
      x_max = point[0]
      right_point = i
    if point[0] < x_min:
      x_min = point[0]
      left_point = i
    if point[1] > y_max:
      y_max = point[1]
      top_point = i
    if point[1] < y_min:
      y_min = point[1]
      bottom_point = i

  log.debug("x_min, x_max, y_min, y_max: %d, %d, %d, %d." % \
      (x_min, x_max, y_min, y_max))
  log.debug("Ext. point indices: (L, R, T, B) %d, %d, %d, %d." % \
      (left_point, right_point, top_point, bottom_point))

  top = Line((x_max, y_max), (x_min, y_max), top_point)
  bottom = Line((x_min, y_min), (x_max, y_min), bottom_point)
  left = Line((x_min, y_max), (x_min, y_min), left_point)
  right = Line((x_max, y_min), (x_max, y_max), right_point)
  sides = [top, bottom, left, right]

  # Create lines for edges of hull.
  hull_edges = {}
  for i in range(0, len(hull)):
    p1 = hull[i]
    p2 = hull[(i + 1) % len(hull)]

    hull_edges[i] = Line(p1, p2, i)

  log.debug("Hull edges: %s." % (hull_edges))

  # Run rotating caliper algorithm.
  best_area = sys.maxint
  best_points = ()
  best_dimensions = ()
  for i in range(0, len(hull)):
    # Find the side with the smallest slope.
    smallest_angle = sys.maxint
    use_side = None
    for side in sides:
      angle = Line.find_angle_between(side, hull_edges[side.index])
      log.debug("Angle between lines: %f." % (angle))
      if angle < smallest_angle:
        smallest_angle = angle
        use_side = side

    # Rotate.
    use_side.slope = hull_edges[use_side.index].slope
    use_side.index = (use_side.index + 1) % len(hull)
    log.debug("New slope: %s." % str((use_side.slope)))
    log.debug("New index: %f." % (use_side.index))

    index = sides.index(use_side)
    if (index == 0 or index == 2):
      parallel = index + 1
    elif (index == 1 or index == 3):
      parallel = index - 1
    orthogonal = range(0, 4)
    orthogonal.remove(index)
    orthogonal.remove(parallel)
    log.debug("Side indices: Main: %d, ||: %d, +: %d, %d." % \
        (index, parallel, orthogonal[0], orthogonal[1]))

    sides[parallel].slope = use_side.slope
    for i in orthogonal:
      sides[i].orthogonal(use_side)

    # The points should be top left, bottom right, top right, and bottom left.
    points, dimensions = rectangle_dimensions(*sides)
    area = dimensions[0] * dimensions[1]
    log.debug("Area: %f." % (area))
    if area < best_area:
      best_area = area
      best_points = points
      best_dimensions = dimensions

  log.debug("Best area: %f\n, Best points: %s\n, Best_dimensions: %s" % \
      (best_area, best_points, best_dimensions))

  return best_points, best_dimensions

# Given a set of points, this function determines the robot's angle to a
# wall as well as the room's dimensions.
def get_room_stats(points):
  bounding_box, dimensions = ombb(points)

  # Calculate the rotation angle.
  p1 = bounding_box[0]
  p2 = bounding_box[2]
  slope = (p2[1] - p1[1]) / (p2[0] - p1[0])
  # This angle should be to the right of the wall in front of the robot.
  angle = math.degrees(math.atan(slope))

  return angle, dimensions
