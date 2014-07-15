# Allows wheels to be run continuously.

import sys
sys.path.append("..")

from starter import Program

import time

import log
import motors
import rate

class continuous_driving(Program):
  def setup(self):
    self.add_feed("continuous_driving")
    self.add_pipe("control")

  def run(self):
    wheels = motors.Wheels(self)

    last_send = 0
    distance = 0
    new_command = False
    while True:
      rate.rate(0.1)

      # Get new commands.
      if not self.continuous_driving.empty():
        data = self.continuous_driving.get()
        command = data[0]
        timestamp = data[1]
        if time.time() - timestamp > 1:
          log.info(self, "Command too old: " + str(command))
          continue

        log.info(self, "Got new command: " + str(command))
        new_command = True

        if command != "stop":
          right_dir = command["right"]
          left_dir = command["left"]
          speed = command["speed"]
          stop = False
        else:
          stop = True

        if not stop:
          # We assume that speeds are in mm/s, and our target is 10 secs before
          # having to resend.
          distance = speed * 10
          left_dist = distance * left_dir
          right_dist = distance * right_dir
          log.debug(self, "Target distance: %d." % (distance))

      # Run the motors
      if distance:
        if new_command:
          if not stop:
            # We have to send a new command.
            wheels.drive(left_dist, right_dist, speed, block = False)
            last_send = time.time()
          else:
            wheels.stop()
            distance = 0
        else:
          if time.time() - last_send >= 9:
            # Resend it. (It should run for 10 seconds but we give ourselves a
            # cushion.)
            last_send = time.time()
            wheels.drive(left_dist, right_dist, speed, block = False)
      
      new_command = False

# Drives until stopped. Left and right directions are ints. positive = forward,
# negative = backward.
def drive(program, left_dir, right_dir, speed):
  command = {}
  
  if left_dir:
    command["left"] = left_dir / abs(left_dir)
  else:
    command["left"] = 0
  
  if right_dir:
    command["right"] = right_dir / abs(right_dir)
  else:
    command["right"] = 0

  command["speed"] = speed

  program.write_to_feed("continuous_driving", (command, time.time()))

# Stops the motors immediately.
def stop(program):
  program.write_to_feed("continuous_driving", ("stop", time.time()))
