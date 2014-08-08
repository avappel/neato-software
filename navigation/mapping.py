# Interface for building a map of a location.

from programs import log

import motors

import room_analysis

# Represents a single room.
class Room:
  def __init__(self):
    self.wheels = motors.Wheels()

  # Given a scan, aligns the robot parallel to a wall of the room.
  def align_to_wall(self, scan):
    angle, _ = room_analysis.get_room_stats(scan)
    log.info("Got angle of %f degrees." % (angle))

    self.wheels.turn(angle)
