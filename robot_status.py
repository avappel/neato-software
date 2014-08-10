# Keeps track of the status of various parts of the robot.

import platform

# The size of the underlying shared memory array.
array_size = 1

# Local reference to the instance of the program for this process.
program = None

# Whether or not we're actually running on the BeagleBone.
def is_testing():
  machine = platform.machine()
  if "arm" in machine:
    # BeagleBone.
    return False
  else:
    return True

# Whether or not the robot is driving.
def get_driving():
  return program.status_array[0]

def is_driving():
  program.status_array[0] = 1

def is_not_driving():
  program.status_array[0] = 0
