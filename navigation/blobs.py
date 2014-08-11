# Separates LIDAR data into blobs.

from programs import log

from operator import itemgetter

import room_analysis
import utilities

class Blob:
  def __init__(self, points = []):
    self.points = points

  def __str__(self):
    return str(self.points)

  # Add a point to the blob.
  def add_point(self, point):
    self.points.append(point)

  # Find the line of best fit for this blob.
  def fit_line(self):
    return utilities.fit_line(self.points)

  # Find what blob this point belongs to.
  @staticmethod
  def find_blob(point, all_blobs):
    for blob in all_blobs:
      if point in blob.points:
        return blob

    return None

# Find blobs in a collection of points.
def find_blobs(points):
  log.debug("Starting blob finder...")

  # How close points have to be to be in the same blob.
  blob_threshold = 300

  # Sort points by x coordinates.
  sort = sorted(points, key = itemgetter(0))
  # Add "used" flag to list.
  x_order = []
  for item in sort:
    x_order.append([item, False])

  # For each point, find all the ones that are close to it.
  blobs = []
  for index in range(0, len(x_order)):
    point = x_order[index][0]

    # Find a subset of the points that are possibly part of this blob.
    possible = []

    # First do it by x's.
    radius = 1
    none_lower = False
    none_higher = False
    while (not (none_lower and none_higher)):
      if index - radius < 0:
        none_lower = True
      if index + radius >= len(x_order):
        none_higher = True

      if not none_lower:
        lower = x_order[index - radius]
        value = lower[0]
        used = lower[1]

        if point[0] - value[0] < blob_threshold:
          if not used:
            possible.append(index - radius)
        else:
          none_lower = True

      if not none_higher:
        higher = x_order[index + radius]
        value = higher[0]
        used = higher[1]

        if value[0] - point[0] < blob_threshold:
          if not used:
            possible.append(index + radius)
        else:
          none_higher = True

      radius += 1

    # Now see if any of them work with the y value as well.
    to_delete = []
    for candidate_index in possible:
      candidate = x_order[candidate_index][0]
      if abs(point[1] - candidate[1]) > blob_threshold:
        # This point can't work.
        to_delete.append(candidate_index)
    for delete in to_delete:
      possible.remove(delete)

    # And now we have points that it is worth actually checking the distance on.
    blob = Blob.find_blob(point, blobs)

    for candidate_index in possible:
      candidate = x_order[candidate_index][0]

      if utilities.distance(point, candidate) < blob_threshold:
        # This is part of the blob.
        if blob:
          # Add candidate to our existing blob.
          blob.add_point(candidate)
        else:
          # Make a new blob.
          blobs.append(Blob([point, candidate]))

        # We'll get to each candidate later as the point we're checking, so we can
        # flag it as used.
        x_order[candidate_index][1] = True

    # We can also get rid of the original point, because we've already found
    # everything close to it.
    x_order[index][1] = True

  for blob in blobs:
    log.debug("Found blob: %s." % (blob))
  return blobs
