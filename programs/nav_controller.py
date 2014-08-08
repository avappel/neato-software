# Attempts to navigate using the lidar sensor.

from __future__ import division

import math
import sys
sys.path.append("..")

from programs import log
from rate import Rate
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

class nav_controller(Program):
  # How much "wiggle" is tolerated between points until we say there is a
  # doorway.
  doorway_threshold = 800

  def setup(self):
    self.add_pipe("control")
    self.add_feed("navigation")

  def run(self):
    self.map_building = False
    self.lds = None

    rate = Rate()

    while True:
      rate.rate(1)

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

# Enables map building mode.
def enable_map_building(program):
  program.write_to_feed("navigation", {"map_building": True})

def disable_map_building(program):
  program.write_to_feed("navigation", {"map_building": False})
