import sys
sys.path.append("..")

from navigation import filters, mapping, utilities
from starter import Program

import motors
import sensors
import slam_controller

class test_navigation(Program):
  def setup(self):
    self.add_pipe("control")
    self.add_pipe("slam_controller")

  def run(self):
    lds = sensors.LDS()
    scan = lds.get_scan()
    scan = filters.remove_outliers(scan)
    scan = utilities.to_rectangular(scan)

    room = mapping.Room()
    room.align_to_wall(scan)

    wheels = motors.Wheels()
    slam_controller.start()

    wheels.drive(100, 100, 300)
    print slam_controller.get_displacement()

    wheels.drive(-100, -100, 300)
    print slam_controller.get_displacement()

    slam_controller.stop()
