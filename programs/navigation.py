# Attempts to navigate using the lidar sensor.

from __future__ import division

import math
import sys
sys.path.append("..")

from programs import log
from starter import Program

import sensors
import time

# Find the distance between two polar points.
def polar_distance(r1, t1, r2, t2):
  return (r1 ** 2 + r2 ** 2 - \
      2 * r1 * r2 * math.cos(math.radians(t1 - t2))) ** (1 / 2)

# Convert a polar pair to a rectangular pair.
def rectangular_pair(r, t):
  x = r * math.cos(math.radians(t))
  y = r * math.sin(math.radians(t))

  return (x, y)

class navigation(Program):
  # How much "wiggle" is tolerated between points until we say there is a
  # doorway.
  doorway_threshold = 800

  def setup(self):
    self.add_pipe("control")
    self.add_feed("navigation")

  def run(self):
    self.map_building = False
    self.lds = None

    while True:
      if not self.navigation.empty():
        command = self.navigation.get()

        if command["map_building"]:
          self.map_building = True
          log.info("Enabling map building mode.")
          self.lds = sensors.LDS()
        else:
          self.map_building = False
          log.info("Disabling map building mode.")
          self.lds = None

      # Attempt to map out the building we're in.
      if self.map_building:
        # Find the shape of the room we're in.
        print self.__room_shape()
        time.sleep(5)

  # Finds the shape of the room using the LIDAR.
  def __room_shape(self):
    scan = self.lds.get_scan()
    if scan:
      scan = self.__clean_scan(scan)
      #doorways, scan = self.__find_doorways(scan)
      #print "Doorways: " + str(doorways)

      scan = self.__to_rectangular(scan)
      corners = self.__find_corners(scan)

      dimension_x = corners[0][0] - corners[1][0]
      dimension_y = corners[0][1] - corners[2][1]
      print (dimension_x / 1000, dimension_y / 1000)

      return corners

  # Finds corners in a scan.
  def __find_corners(self, scan):
    # Find the most extreme points in both x and y.
    max_x = 0
    min_x = 0
    max_y = 0
    min_y = 0

    for pair in scan:
      max_x = max(max_x, pair[0])
      min_x = min(min_x, pair[0])
      max_y = max(max_y, pair[1])
      min_y = min(min_y, pair[1])

    # Create a rectangle incorporating these lines.
    corner_1 = (max_x, max_y)
    corner_2 = (min_x, max_y)
    corner_3 = (min_x, min_y)
    corner_4 = (max_x, min_y)

    return (corner_1, corner_2, corner_3, corner_4)

  # Finds doorways in a polar scan.
  def __find_doorways(self, scan):
    last_angle = ()
    doorways = []
    current_doorway = []

    for angle in range(0, 360):
      if angle in scan.keys():
        if not last_angle:
          last_angle = angle
          continue

        # Skip over any gaps.
        if angle - last_angle > 2:
          current_doorway = []
          last_angle = angle
          continue

        location = scan[angle][0]
        last_location = scan[last_angle][0]

        distance = polar_distance(last_location, last_angle,
            location, angle)
        if distance >= self.doorway_threshold:
          # We found a doorway.
          if (len(current_doorway) == 1 and location - last_location > 0):
            current_doorway.append(angle)
          elif (len(current_doorway) != 1 and location - last_location < 0):
            # We found the end of a doorway.
            doorways.append(current_doorway)
            current_doorway = []
        else:
          if current_doorway:
            # This point is part of a doorway.
            current_doorway.append(angle)

        last_angle = angle

    ret = []
    for doorway in doorways:
      for angle in doorway:
        # Convert the points to rectangular form.
        ret.append(rectangular_pair(scan[angle][0], angle))
        # Remove the points from the original scan.
        scan.pop(angle, None)

    return (ret, scan)

  # Convers the polar data from the sensor into rectangular form.
  def __to_rectangular(self, scan):
    ret = []

    for key in scan.keys():
      ret.append(rectangular_pair(scan[key][0], key))

    return ret

  # Removes outliers and crazy numbers from the polar scan.
  def __clean_scan(self, scan):
    # Compute some statistics for our scan.
    mean = 0
    standard_deviation = 0
    total = 0
    for value in scan.items():
      total += 1
      mean += value[0]
    mean /= total

    for value in scan.items():
      standard_deviation += (value[0] - mean) ** 2
    standard_deviation /= total
    standard_deviation = standard_deviation ** (1 / 2)

    print "Mean: " + str(mean)
    print "StdDev: " + str(standard_deviation)

    # Remove angles near large amounts of errors that are outliers.
    ret = {}
    last_error = 0
    for angle in range(0, 360):
      if angle in scan.keys():
        distance = scan[angle][0]
        if abs(distance - mean) > standard_deviation:
          # This is an outlier.
          if angle - last_error > 4:
            # This not near an error area, so it's probably okay.
            ret[angle] = scan[angle]
        else:
          ret[angle] = scan[angle]

      else:
        last_error = angle

    return ret

# Enables map building mode.
def enable_map_building(program):
  program.write_to_feed("navigation", {"map_building": True})

def disable_map_building(program):
  program.write_to_feed("navigation", {"map_building": False})
