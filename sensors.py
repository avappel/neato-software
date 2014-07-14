# Interfaces with neato command line.

import serial_api as control

from programs import log

import rate

# Represents LDS sensor, and allows user to control it.
class LDS:
  def __init__(self, program):
    self.program = program
    self.ready = False

    control.send_command(self.program, "SetLDSRotation on")
  
  def __del__(self):
    control.send_command(self.program, "SetLDSRotation off")
    LDS.spun_up = False

  # Wait for sensor to spin up.
  def __spin_up(self):
    if not self.ready:
      log.info(self.program, "Waiting for LDS spinup.")
      if not self.is_active(self.program):
        # Wait for a valid packet.
        while True:
          rate.rate(0.01)

          scan = self.__get_scan()
          if len(scan.keys()) > 1:
            break
        
      self.ready = True
        
      log.info(self.program, "LDS ready.")

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

    packet = self.__get_scan()
    packet.pop("ROTATION_SPEED", None);
    return packet

  @staticmethod
  # Returns whether lds is active and ready to transmit data.
  def is_active(program):
    info = control.get_output(program, "GetMotors")
    mvolts = int(info["Laser_mVolts"])
    return bool(mvolts)

  # Returns the rotation speed of the LDS sensor.
  def rotation_speed(self):
    if not self.is_active(self.program):
      return 0

    return self.__get_scan()["ROTATION_SPEED"]
  
# A class for the analog sensors.
class Analog:
  def __init__(self, program):
    self.program = program

  def __get_sensors(self, **kwargs):
    return control.get_output(self.program, "GetAnalogSensors", **kwargs)

  # Gets readings from the drop sensors.
  def drop(self, **kwargs):
    info = self.__get_sensors(**kwargs)
    left = int(info["LeftDropInMM"])
    right = int(info["RightDropInMM"])
    
    return (left, right)

  # Returns the battery voltage.
  def battery_voltage(self, **kwargs):
    info = self.__get_sensors(**kwargs)
    voltage = int(info["BatteryVoltageInmV"])

    return voltage

  # Return the charging voltage.
  def charging(self, **kwargs):
    info = self.__get_sensors(**kwargs)
    voltage = int(info["ChargeVoltInmV"])

    return voltage

class Digital:
  def __init__(self, program):
    self.program = program

  def __get_sensors(self, **kwargs):
    return control.get_output(self.program, "GetDigitalSensors", **kwargs)

  # Returns whether or not the wheels are extended.
  def wheels_extended(self, **kwargs):
    while True:
      info = self.__get_sensors(**kwargs)
      try:
        left = bool(int(info["SNSR_LEFT_WHEEL_EXTENDED"]))
        right = bool(int(info["SNSR_RIGHT_WHEEL_EXTENDED"]))
        break
      except KeyError:
        continue
    
    return (left, right)
