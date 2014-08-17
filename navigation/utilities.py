# Useful functions for navigation that are used all over the place.

from __future__ import division

from scipy.optimize import leastsq

import math
import numpy as np

# Convert a pair from polar to rectangular.
def rectangular_pair(r, theta):
  x = r * math.cos(math.radians(theta))
  y = r * math.sin(math.radians(theta))

  return (x, y)

# Convert an entire scan to rectangular.
def to_rectangular(scan):
  ret = []
  for angle in scan.keys():
    ret.append(rectangular_pair(scan[angle][0], angle))

  return ret

# Compute distance between two points
def distance(p1, p2):
  return ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** (1 / 2)

# Use the least squares approximation method to compute a line of best fit for
# input data points. (Returns the slope and intercept.)
def fit_line(points):
  x_values = []
  y_values = []
  for point in points:
    x_values.append(point[0])
    y_values.append(point[1])
  x_values = np.array(x_values)
  y_values = np.array(y_values)

  def residuals(p, y, x):
    m, b = p
    error = y - (m * x + b)
    return error

  # Use two points to calculate initial parameters.
  m = (points[1][1] - points[0][1]) / (points[1][0] - points[0][0])
  b = points[0][1] - m * points[0][0]
  p0 = [m, b]

  return leastsq(residuals, p0, args = (y_values, x_values))[0]

# Find the point at the intersection of the line and a perpendicular line that
# runs through a specified point.
def landmark_point(point, m, b):
  # Find the intercept of a perpendicular line
  # going through the point.
  b_perp = point[1] + (1 / m) * point[0]

  # Find the point of intersection between the two lines.
  x_int = (b - b_perp) / ((-1 / m) - m)
  y_int = m * x_int + b

  return (x_int, y_int)

# Find the shortest distance between a line and a point.
def line_distance(point, m, b):
  intersection = landmark_point(point, m, b)
  return distance(point, intersection)
