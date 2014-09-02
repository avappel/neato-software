# This program is in charge of using the SLAM system to keep tabs on the robot's
# displacement.

from __future__ import division

import math
import sys
import time
sys.path.append("..")

from navigation import slam
from rate import Rate
from starter import Program

import log
import robot_status

class slam_controller(Program):
  def setup(self):
    self.add_feed("slam_controller")
    self.add_pipe("control")

  def run(self):
    rate = Rate()
    nav = None

    # Wait for a command.
    while True:
      if (not nav or not self.slam_controller.empty()):
        command = self.slam_controller.get()

        if "run" in command.keys():
          if command["run"]:
            log.info("Starting SLAM navigation...")
            nav = slam.Slam(command["x"], command["y"], command["theta"])

            # Notify anyone waiting that we're ready.
            for pipe in self.pipes:
              pipe.send({"ready": True})

          else:
            log.info("Stopping SLAM navigation...")
            nav = None
        else:
          if nav:
            if "driving" in command.keys():
              if command["driving"]:
                log.debug("Got started driving hook.")
                print "Started driving: " + str(command["position"])
                nav.started_driving(command["position"], command["timestamp"])
              else:
                log.debug("Got stopped driving hook.")
                print "Stopped driving: " + str(command["position"])
                nav.stopped_driving(command["position"], command["timestamp"])

            elif "displacement" in command.keys():
              if command["displacement"]:
                log.debug("Displacement requested.")

                # Send our displacement.
                pipe = getattr(self, command["program"])
                pipe.send({"displacement": nav.get_displacement()})

            elif "reset" in command.keys():
              if command["reset"] == "position":
                # Reset the robot position.
                log.info("Resetting the robot's position.")
                nav.reset_position()
              elif command["reset"] == "bearing":
                # Reset the robot bearing.
                log.info("Resetting the robot's bearing.")
                nav.reset_bearing()

          else:
            log.warning("Not running command when SLAM isn't running.")

      if nav:
        # Run the Kalman filter periodically.
        rate.rate(0.5)
        print "Updating position..."
        nav.update_position()
        print "Done!"


def __write_driving_status(is_driving, wheel_position):
  try:
    robot_status.program.write_to_feed("slam_controller",
        {"driving": is_driving,
        "position": wheel_position,
        "timestamp": time.time()},
        block = False)
  except RuntimeError:
    log.debug("Not notifying SLAM process because queue is full.")


# These functions can be run by other processes to notify the slam system of
# when the wheels are started and stopped.
def wheels_started(wheel_position):
  __write_driving_status(True, wheel_position)

def wheels_stopped(wheel_position):
  __write_driving_status(False, wheel_position)

# Tell SLAM controller to start keeping track of position. Start_position sets
# the starting position for the robot.
def start(start_x = 0, start_y = 0, start_bearing = math.pi / 2):
  robot_status.program.write_to_feed("slam_controller",
      {"run": True,
      "x": start_x,
      "y": start_y,
      "theta": start_bearing})

  # Wait for the LIDAR to get ready. (It will tell us.)
  while True:
    status = robot_status.program.slam_controller.recv()
    if status["ready"]:
      break

  log.info("LIDAR is ready for SLAM.")

# Tell SLAM controller to stop keeping track of position.
def stop():
  robot_status.program.write_to_feed("slam_controller", {"run": False})

# Get the current displacement of the robot.
def get_displacement():
  program_name = robot_status.program.__class__.__name__
  robot_status.program.write_to_feed("slam_controller",
      {"displacement": True,
      "program": program_name})

  return robot_status.program.slam_controller.recv()["displacement"]

# Resets the position of the robot.
def reset_position():
  robot_status.program.write_to_feed("slam_controller", {"reset": "position"})

# Resets the bearing of the robot.
def reset_bearing():
  robot_status.program.write_to_feed("slam_controller", {"reset": "bearing"})
