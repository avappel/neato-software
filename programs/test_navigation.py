import sys
sys.path.append("..")

#from programs import navigation
from navigation import mapping, utilities
from starter import Program

import motors
import sensors

class test_navigation(Program):
  def setup(self):
    self.add_pipe("control")

  def run(self):
    #navigation.enable_map_building(self)

    lds = sensors.LDS()
    scan = lds.get_scan()
    scan = utilities.to_rectangular(scan)

    room = mapping.Room()
    room.align_to_wall(scan)
