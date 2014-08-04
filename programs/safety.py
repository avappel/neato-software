# This program should be running always to insure that the robot doesn't damage
# itself.

import sys
sys.path.append("..")

from starter import Program

import log
import motors
import rate
import sensors
import serial_api

class safety(Program):
  def setup(self):
    self.add_pipe("control")

  def run(self):
    self.wheels = motors.Wheels(self)
    self.enabled = True

    analog = sensors.Analog(self)
    digital = sensors.Digital(self)
    check_drop = True
    
    while True:
      rate.rate(0.5)
     
      # Check that we're not about to drive off a drop.
      try:
        left_drop, right_drop = analog.drop(stale_time = 0)
        if not self.enabled:
          log.info(self, "Reenabling wheels...")
          self.__enable()

      except ValueError:
        if self.enabled:
          log.warning(self, "Can't get reliable readings. Disabling motors...")
          self.__disable()
          continue

      log.debug(self, "Drop sensor readings: %d, %d." % (left_drop, right_drop))
      
      # Disable the wheels if someone picked us up.
      left, right = digital.wheels_extended(stale_time = 0.5)
      if ((left or right) and self.enabled):
        log.info(self, "Wheels extended, disabling.")
        self.__disable()
      elif ((not (left or right)) and not self.enabled):
        log.info(self, "Wheels not extended, enabling.")
        self.__enable()
      # Run drop handler.
      elif (max(left_drop, right_drop) < 25000 and self.enabled):
        log.info(self, "Detected drop, running drop handler.")
        self.__drop_handler()
            
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
    serial_api.freeze()
    self.wheels.disable()
    self.enabled = False

  # Enables motors.
  def __enable(self):
    self.wheels.enable()
    serial_api.unfreeze()
    self.enabled = True
