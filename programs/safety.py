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
    analog = sensors.Analog(self)
    digital = sensors.Digital(self)
    check_extended = 1
    wheels_extended = False
    check_drop = True
    
    while True:
      rate.rate(0.01)
     
      # Check that we're not about to drive off a drop.
      left_drop, right_drop = analog.drop(stale_time = 0)
      log.debug(self, "Drop sensor readings: %d, %d." % (left_drop, right_drop))
      
      # Disable the wheels if someone picked us up.
      left, right = digital.wheels_extended(stale_time = 0.5)
      if ((left or right) and not wheels_extended):
        log.info(self, "Wheels extended, disabling.")
        serial_api.freeze(self)
        self.wheels.disable()
        wheels_extended = True
      elif ((not (left or right)) and wheels_extended):
        log.info(self, "Wheels not extended, enabling.")
        self.wheels.enable()
        serial_api.unfreeze(self)
        wheels_extended = False
      elif (max(left_drop, right_drop) < 25000 and not wheels_extended):
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
