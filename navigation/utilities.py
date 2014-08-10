# Useful functions for navigation that are used all over the place.

from __future__ import division

import math

# Convert a pair from polar to rectangular.
def rectangular_pair(r, theta):
  x = r * math.cos(math.radians(theta))
  y = r * math.sin(math.radians(theta))

  return (x, y)

# Convert an entire scan to rectangular.
def to_rectangular(scan):
  ret = []
  for angle in scan.keys():
    ret.append((angle, rectangular_pair(scan[angle][0], angle)))

  return ret

# Compute distance between two points
def distance(p1, p2):
  return ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** (1 / 2)
