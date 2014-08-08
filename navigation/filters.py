# Filtering for LDS data.

from __future__ import division

from programs import log

# A simple filter that removes anything not within the standard deviation from
# a polar scan.
def remove_outliers(scan):
    # Compute some statistics for our scan.
    mean = 0
    standard_deviation = 0
    total = 0
    for value in scan.items():
      total += 1
      mean += value[0]
    mean /= total

    for value in scan.items():
      standard_deviation += (value[1][0] - mean) ** 2
    standard_deviation /= total
    standard_deviation = standard_deviation ** (1 / 2)

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

