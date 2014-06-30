# Interfaces with neato command line.

import serial
import time

stream = serial.Serial(port = "/dev/ttyACM0", timeout = 0)

# Enable test mode on the neato.
stream.write("testmode on\n")

# Represents LDS sensor, and allows user to control it.
class LDS:
  spun_up = False

  def __init__(self):
    send_command("SetLDSRotation on")
  
  def __del__(self):
    send_command("SetLDSRotation off")
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
    packet = get_output("GetLDSScan")

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

# Gets results from a command on the neato.
def get_output(command):
  stream.flushInput()
  send_command(command)

  response = ""
  start = False
  while True:
    line = stream.read(1024)
    if start:
      response += line

    if command in line:
      start = True

    # All responses end with this character.
    if (response != "" and response[-1] == ""):
      # Get rid of end character and newline.
      response = response[:-2]

      # All responses are CSVs, so we can turn them into a nice little dict.
      lines = response.split("\r\n")
      ret = {}
      for line in lines:
        split = line.split(",")
        if len(split) > 2:
          ret[split[0]] = split[1:]
        else:
          ret[split[0]] = split[1]

      return ret

# Sends a command to the neato.
def send_command(command):
  stream.write(command + "\n")

class Wheels:
  enabled = False

  def __init__(self):
    self.enable()

  def __del__(self):  
    self.disable()

  # Waits for motors to be stopped.
  def __wait_for_stop(self):
    while self.get_wheel_rpms()[0] != 0:
      time.sleep(0.01)
    while self.get_wheel_rpms()[1] != 0:
      time.sleep(0.01)

  # Enables both drive motors.
  def enable(self, block = True):
    if not self.enabled:
      send_command("SetMotor LWheelEnable RWheelEnable")
      self.enabled = True

      if block:
        self.__wait_for_stop()

  # Disables both drive motors.
  def disable(self):
    if self.enabled:
      send_command("SetMotor LWheelDisable RWheelDisable")
      self.enabled = False

  # A version of drive that employs the LDS in order to not crash into things.
  def safe_drive(self, left_dist, right_dist, speed):
    # Max speed here is 200 for safety reasons.
    speed = min(speed, 200)

    lds = LDS()
    paused = True
    watching = {}
    danger = []
    initial_distance = self.get_distance()
    
    while True:
      # Check if we're done.
      if not paused:
        rpms = self.get_wheel_rpms()
        if max(rpms[0], rpms[1]) == 0:
          break

      # Get newest data from LDS.
      packet = lds.get_scan()
      packet.pop("ROTATION_SPEED", None)
      
      # Anything fewer than a certain distance away we want to watch.
      watch_distance = 450
      for key in packet.keys():
        if (packet[key][0] < watch_distance and key not in watching.keys()):
          watching[key] = packet[key][0]
        if packet[key][0] > watch_distance:
          # Check if this is something that moved away.
          if key in danger:
            danger.remove(key)
          if key in watching.keys():
            watching.pop(key, None)

      # Keys that caused errors get automatically removed from the danger list.
      for key in danger:
        if key not in packet.keys():
          danger.remove(key)

      # Check if anything we're watching got any closer.
      to_delete = []
      for key in watching.keys():
        try:
          new = packet[key][0]
        except KeyError:
          continue

        dx = new - watching[key]
        if dx < 0:
          # It got closer. We should stop moving.
          to_delete.append(key)
          if key not in danger:
            danger.append(key)
      
      for key in to_delete:
        watching.pop(key, None)

      # Stop the motors if we have to.
      if (len(danger) and not paused):
        self.stop()
        paused = True
      if (not len(danger) and paused):
        new_distance = self.get_distance()
        left_distance = new_distance[0] - initial_distance[0]
        right_distance = new_distance[1] - initial_distance[1]
        left_to_go = left_dist - left_distance
        right_to_go = right_dist - right_distance
        self.drive(left_to_go, right_to_go, speed, block = False)

        paused = False

      # Even at max speed, it will take at least this long for anything to
      # change.
      time.sleep(0.03)
  
  # Instruct the drive motors to move.
  def drive(self, left_dist, right_dist, speed, block = True):
    send_command("SetMotor %d %d %d" % (left_dist, right_dist, speed))
  
    if block:
      self.__wait_for_stop()
      
  # Stops both drive motors immediately.
  def stop(self):
    send_command("SetMotor -1 -1 300")

  # Get RPMs of wheel motors.
  def get_wheel_rpms(self):
    info = get_output("GetMotors")
    left = int(info["LeftWheel_RPM"])
    right = int(info["RightWheel_RPM"])
    return (left, right)
  
  # Get the distance traveled by each wheel.
  def get_distance(self):
    info = get_output("GetMotors")
    left = int(info["LeftWheel_PositionInMM"])
    right = int(info["RightWheel_PositionInMM"])
    return (left, right)

# Shutdown the robot. (NOTE: This will kill power to the control system.)
def shutdown():
  send_command("SetSystemMode Shutdown")

# Put the robot on standby.
def standby():
  send_command("SetSystemMode Standby")
