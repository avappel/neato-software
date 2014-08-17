# Handles operations concerning motors on the robot.

import time

from programs import log
from rate import Rate
from sensors import LDS

import math
import robot_status
import serial_api as control

class Wheels:
  enabled = False

  def __init__(self):
    self.enable()

  # Waits for motors to be stopped.
  def __wait_for_stop(self):
    while self.get_wheel_rpms(stale_time = 0)[0] != 0:
      time.sleep(0.1)
    while self.get_wheel_rpms(stale_time = 0)[1] != 0:
      time.sleep(0.1)

    robot_status.is_not_driving()

  # Enables both drive motors.
  def enable(self):
    if not self.enabled:
      control.send_command("SetMotor LWheelEnable RWheelEnable")
      self.enabled = True

  # Disables both drive motors.
  def disable(self):
    if self.enabled:
      control.send_command("SetMotor LWheelDisable RWheelDisable")
      self.enabled = False
      robot_status.is_not_driving()

  # A version of drive that employs the LDS in order to not crash into things.
  def safe_drive(self, left_dist, right_dist, speed):
    # Max speed here is 200 for safety reasons.
    speed = min(speed, 200)

    lds = LDS()
    paused = True
    watching = {}
    danger = []
    initial_distance = self.get_distance(stale_time = 0)

    rate = Rate()

    while True:
      # Even at max speed, it will take at least this long for anything to
      # change.
      rate.rate(0.03)

      # Check if we're done.
      if not paused:
        rpms = self.get_wheel_rpms(stale_time = 0)
        if max(rpms[0], rpms[1]) == 0:
          log.info("Safe drive: Exiting loop.")
          break

      # Get newest data from LDS.
      packet = lds.get_scan()

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
        log.warning("Stopping due to obstacle.")
        self.stop()
        paused = True
      if (not len(danger) and paused):
        new_distance = self.get_distance()
        left_distance = new_distance[0] - initial_distance[0]
        right_distance = new_distance[1] - initial_distance[1]
        left_to_go = left_dist - left_distance
        right_to_go = right_dist - right_distance
        log.info("Safe drive: SetMotors %d %d %d" % \
            (left_to_go, right_to_go, speed))
        self.drive(left_to_go, right_to_go, speed, block = False)

        paused = False

  # Instruct the drive motors to move.
  def drive(self, left_dist, right_dist, speed, block = True):
    robot_status.is_driving()
    control.send_command("SetMotor %d %d %d" % (left_dist, right_dist, speed))

    if block:
      self.__wait_for_stop()

  # Instructs the robot to turn by a certain number of degrees. Positive for
  # counter-clockwise, negative for clockwise.
  def turn(self, angle):
    circumference = robot_status.ROBOT_WIDTH * math.pi
    distance = angle * circumference / 360

    speed = abs(angle) * 300 / 90
    speed = min(speed, 300)

    self.drive(-distance, distance, speed)

  # Stops both drive motors immediately.
  def stop(self):
    control.send_command("SetMotor -1 -1 300")
    robot_status.is_not_driving()

  # Get RPMs of wheel motors.
  def get_wheel_rpms(self, **kwargs):
    info = control.get_output("GetMotors", **kwargs)
    left = int(info["LeftWheel_RPM"])
    right = int(info["RightWheel_RPM"])
    return (left, right)

  # Get the distance traveled by each wheel.
  def get_distance(self, **kwargs):
    info = control.get_output("GetMotors", **kwargs)
    left = int(info["LeftWheel_PositionInMM"])
    right = int(info["RightWheel_PositionInMM"])
    return (left, right)
