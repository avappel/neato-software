import sys
sys.path.append("..")

from programs import navigation
from starter import Program

class test_navigation(Program):
  def run(self):
    navigation.enable_map_building(self)
