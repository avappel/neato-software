# Keeps track of the status of various parts of the robot.

from programs import log

# The size of the underlying shared memory array.
array_size = 1

# Whether or not the robot is driving.
def GetDriving(program):
  return program.status_array[0]

def IsDriving(program):
  log.debug(program, "Driving.")
  program.status_array[0] = 1

def IsNotDriving(program):
  log.debug(program, "Not driving.")
  program.status_array[0] = 0
