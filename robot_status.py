# Keeps track of the status of various parts of the robot.

from programs import log

# The size of the underlying shared memory array.
array_size = 1

# Local reference to the instance of the program for this process.
program = None

# Whether or not the robot is driving.
def GetDriving():
  return program.status_array[0]

def IsDriving():
  log.debug("Driving.")
  program.status_array[0] = 1

def IsNotDriving():
  log.debug("Not driving.")
  program.status_array[0] = 0
