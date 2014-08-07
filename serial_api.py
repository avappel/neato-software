# Versions of API interface functions for use by the user. The first argument is
# a program subclass instance.

from starter import Program

import robot_status

# Represents a command for the control program.
class Command:
  def __init__(self, command = None, stale_time = 10):
    program = robot_status.program

    # What program it came from.
    self.Source = program.__class__.__name__
    # Whether we want output.
    self.Output = False
    # What the actual command is.
    self.Command = command
    # Represents a custom cache stale time to use.
    self.Stale = stale_time

# Get the output of a command.
def get_output(*args, **kwargs):
  program = robot_status.program

  command = Command(*args, **kwargs)
  command.Output = True

  Program.write_to_feed("control", command)
  # Write to the feed but read from the pipe.
  return program.control.recv()

# Run a command without output.
def send_command(*args, **kwargs):
  command = Command(*args, **kwargs)
  command.Output = False

  Program.write_to_feed("control", command)

# Freezes the control program until the same program the originally called
# freeze calls unfreeze. When the control program is frozen, the freezing
# process can still send commands to it, but nothing else can.
def freeze():
  command = Command("freeze")
  Program.write_to_feed("control", command)

# Unfreezes the control program. If the control program has not been frozen by
# this program, it has no effect.
def unfreeze():
  command = Command("unfreeze")
  Program.write_to_feed("control", command)
