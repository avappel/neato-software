# This program should be running always to insure that the robot doesn't damage
# itself.

import sys
sys.path.append("..")

from rate import Rate
from starter import Program

import log
import motors
import robot_status
import sensors
import serial_api

class safety(Program):
  def setup(self):
    self.add_pipe("control")

  def run(self):
    self.wheels = motors.Wheels()
    self.enabled = True
    stale_data = False

    analog = sensors.Analog()
    digital = sensors.Digital()

    rate = Rate()

    while True:
      rate.rate(0.1)

      # Check that we're not about to drive off a drop.
      if (robot_status.get_driving() or not self.enabled):
        try:
          left_drop, right_drop = analog.drop(stale_time = 0)
          if stale_data:
            log.info("Reenabling wheels...")
            self.__enable()
            stale_data = False

        except ValueError:
          if not stale_data:
            log.warning("Can't get reliable readings. Disabling motors...")
            self.__disable()
            stale_data = True
            continue

        if (max(left_drop, right_drop) <= 25000 and self.enabled):
          log.debug("Drop sensor readings: %d, %d." % (left_drop, right_drop))

          left, right = digital.wheels_extended(stale_time = 0.5)
          if (not left and not right):
            log.info("Detected drop, running drop handler.")
            self.__drop_handler()
          else:
            log.info("Robot picked up, disabling.")

            self.__disable()
        elif (max(left_drop, right_drop) > 25000 and not self.enabled):
          # We're back on the ground.
          log.debug("Drop sensor readings: %d, %d." % (left_drop, right_drop))

          log.info("Back on ground, continuing...")
          self.__enable()

  # Handles a detected drop.
  def __drop_handler(self):
    # Freeze the control program.
    serial_api.freeze()

    # Stop motors and navigate away from the drop.
    self.wheels.stop()
    self.wheels.drive(-500, -500, 100)
    self.wheels.turn(90)

    # Unfreeze control program and return to normal operation.
    serial_api.unfreeze()

  # Disables motors.
  def __disable(self):
    serial_api.freeze()
    self.wheels.disable()
    self.enabled = False

  # Enables motors.
  def __enable(self):
    self.wheels.enable()
    serial_api.unfreeze()
    self.enabled = True
