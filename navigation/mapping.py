# Interface for building a map of a location.

from programs import log

import motors

import blobs
import filters
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

    # Find the best wall, and line up to that.
    wall_scores = []
    for wall in walls.keys():
      if walls[wall] == None:
        score = len(wall.points)
      else:
        score = len(wall.points) + walls[wall]
      print score
      log.debug("Wall score: %f" % (score))
      wall_scores.append(score)

    best = walls.keys()[wall_scores.index(max(wall_scores))]

    angle, _ = room_analysis.get_room_stats(best.points)
    log.info("Got angle of %f degrees." % (angle))

    self.wheels.turn(angle)
