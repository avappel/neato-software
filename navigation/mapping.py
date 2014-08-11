# Interface for building a map of a location.

import math
import sys

from programs import log

import blobs
import filters
import motors
import room_analysis

# Represents a single room.
class Room:
  def __init__(self):
    self.wheels = motors.Wheels()

  # Given a scan, aligns the robot parallel to a wall of the room.
  def align_to_wall(self, scan):
    # Find walls in the scan.
    all_blobs = blobs.find_blobs(scan)
    walls = filters.find_walls(all_blobs)

    if not walls:
      log.error("Could not find any walls.")
      return

    # Line up with the best wall we have.
    best_quality = -sys.maxint
    best_wall = None
    for wall in walls:
      if wall[2] > best_quality:
        best_quality = wall[2]
        best_wall = wall

    # Find the angle of the wall.
    angle = math.degrees(math.atan(best_wall[0]))
    log.info("Got angle of %f degrees." % (angle))

    self.wheels.turn(angle)
