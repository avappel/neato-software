import sys
import time
sys.path.append("..")

from starter import Program

import motors
import sensors

class neato_test(Program):
  def setup(self):
    self.add_pipe("control")

  def run(self):
    #l = sensors.LDS(self)
    time.sleep(10)
    wheels = motors.Wheels(self)
    wheels.safe_drive(-500, -500, 200)
    #wheels.safe_drive(300, -300, 50)
    #wheels.safe_drive(-300, 300, 100)
    #wheels.safe_drive(-500, -500, 200)
