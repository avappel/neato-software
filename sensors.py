# Interfaces with neato command line.

import serial_api as control

from programs import log

import rate

# Represents LDS sensor, and allows user to control it.
class LDS:
  spun_up = False

  def __init__(self, program):
    self.program = program

    control.send_command(self.program, "SetLDSRotation on")
  
  def __del__(self):
    control.send_command(self.program, "SetLDSRotation off")
    LDS.spun_up = False

  # Wait for sensor to spin up.
  def __spin_up(self):
    log.debug(self.program, "Waiting for LDS spinup.")
    if not LDS.spun_up:
      # Wait for a valid packet.
      while True:
        rate.rate(0.01)

        scan = self.__get_scan()
        if len(scan.keys()) > 1:
          break
      
      LDS.spun_up = True
    log.debug(self.program, "LDS ready.")

  # Helper to get and parse a complete scan packet.
  def __get_scan(self):
    packet = control.get_output(self.program, "GetLDSScan")

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
      else:
        log.debug(self.program, "Error %s in LDS reading for angle %s." % \
            (packet[key][2], key))

    return ret

  # Returns a usable scan packet to the user.
  def get_scan(self):
    # Make sure sensor is ready.
    self.__spin_up()

    return self.__get_scan()

  # Returns the rotation speed of the LDS sensor.
  def rotation_speed(self):
    return self.__get_scan()["ROTATION_SPEED"]

# A class for the analog sensors.
class Analog:
  def __init__(self, program):
    self.program = program

  def __get_sensors(self):
    return control.get_output(self.program, "GetAnalogSensors")

  # Gets readings from the drop sensors.
  def drop(self):
    info = self.__get_sensors()
    left = int(info["LeftDropInMM"])
    right = int(info["RightDropInMM"])
    
    return (left, right)

class Digital:
  def __init__(self, program):
    self.program = program

  def __get_sensors(self):
    return control.get_output(self.program, "GetDigitalSensors")

  # Returns whether or not the wheels are extended.
  def wheels_extended(self):
    info = self.__get_sensors()
    left = bool(int(info["SNSR_LEFT_WHEEL_EXTENDED"]))
    right = bool(int(info["SNSR_RIGHT_WHEEL_EXTENDED"]))
    
    return (left, right)
