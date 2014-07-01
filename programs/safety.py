# This program should be running always to insure that the robot doesn't damage
# itself.

import sys
sys.path.append("..")

from starter import Program

import motors
import rate
import sensors

class safety(Program):
  def setup(self):
    self.add_pipe("control")

  def run(self):
    analog = sensors.Analog(self)
    wheels = motors.Wheels(self)
    
    while True:
      rate.rate(0.5)
      
      # Check that we're not about to drive off a drop.
      left, right = analog.drop()
      if max(left, right) >= 80:
        wheels.stop()
