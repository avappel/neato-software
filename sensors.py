# Interfaces with neato command line.

import time

import control

# Represents LDS sensor, and allows user to control it.
class LDS:
  spun_up = False

  def __init__(self):
    control.send_command("SetLDSRotation on")
  
  def __del__(self):
    control.send_command("SetLDSRotation off")
    LDS.spun_up = False

  # Wait for sensor to spin up.
  def __spin_up(self):
    if not LDS.spun_up:
      # Wait for a valid packet.
      while True:
        scan = self.__get_scan()
        if len(scan.keys()) > 1:
          break
        
        time.sleep(0.01)
      
      LDS.spun_up = True

  # Helper to get and parse a complete scan packet.
  def __get_scan(self):
    packet = control.get_output("GetLDSScan")

    # Get rid of help message.
    packet.pop("AngleInDegrees", None)

    # Add rotation speed.
    ret = {}
    ret["ROTATION_SPEED"] = float(packet["ROTATION_SPEED"])
    packet.pop("ROTATION_SPEED", None)

    # Discard any errors.
    for key in packet.keys():
      if int(packet[key][2]) == 0:
        ret[int(key)] = [int(x) for x in packet[key]]

    return ret

  # Returns a usable scan packet to the user.
  def get_scan(self):
    # Make sure sensor is ready.
    self.__spin_up()

    return self.__get_scan()

  # Returns the rotation speed of the LDS sensor.
  def rotation_speed(self):
    return self.__get_scan()["ROTATION_SPEED"] 
