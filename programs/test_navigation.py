import sys
sys.path.append("..")

from navigation import filters, mapping, slam, utilities
from starter import Program

import motors
import sensors

class test_navigation(Program):
  def setup(self):
    self.add_pipe("control")

  def run(self):
    lds = sensors.LDS()
    scan = lds.get_scan()
    scan = filters.remove_outliers(scan)
    scan = utilities.to_rectangular(scan)

    room = mapping.Room()
    room.align_to_wall(scan)

    wheels = motors.Wheels()

    nav = slam.Slam()
    nav.started_driving()
    wheels.drive(0, 100, 300)
    nav.stopped_driving()
    print nav.get_displacement()

    nav.started_driving()
    wheels.drive(-300, -300, 300)
    nav.stopped_driving()
    print nav.get_displacement()
