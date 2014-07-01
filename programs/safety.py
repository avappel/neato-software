# This program should be running always to insure that the robot doesn't damage
# itself.

import sys
sys.path.append("..")

from starter import Program

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
    
    while True:
      rate.rate(0.5)
      
      # Check that we're not about to drive off a drop.
      left, right = analog.drop()
      if max(left, right) >= 80:
        self.__drop_handler()

      # Disable the wheels if someone picked us up.
      if check_extended >= 2:
        left, right = digital.wheels_extended()
        if ((left or right) and not wheels_extended):
          serial_api.freeze(self)
          wheels.disable()
          wheels_extended = True
        elif ((not (left or right)) and wheels_extended):
          wheels.enable()
          serial_api.unfreeze(self)
          wheels.extended = False
          
        check_extended = 0
      check_extended += 1

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
