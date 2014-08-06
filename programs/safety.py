# This program should be running always to insure that the robot doesn't damage
# itself.

import sys
sys.path.append("..")

from starter import Program

import log
import motors
import rate
import robot_status
import sensors
import serial_api

class safety(Program):
  def setup(self):
    self.add_pipe("control")

  def run(self):
    self.wheels = motors.Wheels(self)
    self.enabled = True
    stale_data = False

    analog = sensors.Analog(self)
    digital = sensors.Digital(self)
    
    while True:
      rate.rate(0.1)

      # Check that we're not about to drive off a drop.
      if (robot_status.GetDriving(self) or not self.enabled):
        try:
          left_drop, right_drop = analog.drop(stale_time = 0)
          if stale_data:
            log.info(self, "Reenabling wheels...")
            self.__enable()
            stale_data = False

        except ValueError:
          if not stale_data:
            log.warning(self, "Can't get reliable readings. Disabling motors...")
            self.__disable()
            stale_data = True
            continue

        if (max(left_drop, right_drop) <= 25000 and self.enabled):
          log.debug(self, "Drop sensor readings: %d, %d." % (left_drop, right_drop))
          
          left, right = digital.wheels_extended(stale_time = 0.5)
          if (not left and not right):
            log.info(self, "Detected drop, running drop handler.")
            self.__drop_handler()
          else:
            log.info(self, "Robot picked up, disabling.")
            self.__disable()
        elif (max(left_drop, right_drop) > 25000 and not self.enabled):
          # We're back on the ground.
          log.debug(self, "Drop sensor readings: %d, %d." % (left_drop, right_drop))
          
          log.info(self, "Back on ground, continuing...")
          self.__enable()
            
  # Handles a detected drop.
  def __drop_handler(self):
    # Freeze the control program.
    serial_api.freeze(self)

    # Stop motors and navigate away from the drop.
    self.wheels.stop()
    self.wheels.drive(-500, -500, 100)
    # TODO: (daniel) Figure out distance for 90 deg turn.
    self.wheels.drive(150, -150, 300)

    # Unfreeze control program and return to normal operation.
    serial_api.unfreeze(self)

  # Disables motors.
  def __disable(self):
    serial_api.freeze(self)
    self.wheels.disable()
    self.enabled = False

  # Enables motors.
  def __enable(self):
    self.wheels.enable()
    serial_api.unfreeze(self)
    self.enabled = True
