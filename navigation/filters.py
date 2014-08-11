# Filtering for LDS data.

from __future__ import division

from programs import log

import utilities

import numpy as np

# A simple filter that removes anything not within the standard deviation from
# a polar scan.
def remove_outliers(scan):
    # Compute some statistics for our scan.
    distances = [item[1] for item in scan.items()]

    mean = np.mean(distances)
    standard_deviation = np.std(distances)
    log.debug("Mean: %d." % (mean))
    log.debug("Standard Deviation: %d." % (standard_deviation))

    # Remove angles that are outliers.
    ret = {}
    last_error = 0
    for angle in range(0, 360):
      if angle in scan.keys():
        distance = scan[angle][0]
        if abs(distance - mean) > standard_deviation:
          if angle - last_error > 4:
            # We're far enough from an error spot that this is probably okay.
            ret[angle] = scan[angle]
          else:
            log.debug("Removing angle %d with value of %d." % (angle, distance))
        else:
          ret[angle] = scan[angle]

      else:
        last_error = angle

    return ret

# Takes a blobified scan and returns blobs that it thinks are walls.
def find_walls(blobs):
  # The minimum number of points that must lie close to a line for it to be
  # called a wall.
  consensus = 10
  # The maximum distance in mm a point can be from the line
  # before it doesn't count as part of the wall.
  max_distance = 100

  walls = []
  for blob in blobs:
    if len(blob.points) < consensus:
      continue

    slope, intercept = blob.fit_line()
    wall_points = []
    total_distance = 0
    for point in blob.points:
      # Find the distance between the line of best fit and each point.
      distance = utilities.line_distance(point, slope, intercept)
      if distance <= max_distance:
        wall_points.append(point)
        total_distance += distance

    # Now see if we still have at least ten points.
    if len(wall_points) < consensus:
      continue

    mean_distance = total_distance / len(wall_points)

    # Quality is a rough measure of how good of a landmark this wall is.
    quality = 2 * len(wall_points) - mean_distance

    log.debug("Found wall with points: %s." % (wall_points))
    log.debug("Wall quality: %f." % (quality))
    walls.append((slope, intercept, quality))

  return walls
