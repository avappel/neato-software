# Versions of API interface functions for use by the user. The first argument is
# a program subclass instance.

# Get the output of a command.
def get_output(program, command):
  name = program.__class__.__name__
  program.write_to_feed("control", (name, True, command))
  # Write to the feed but read from the pipe.
  return program.control.recv()

# Run a command without output.
def send_command(program, command):
  name = program.__class__.__name__
  program.write_to_feed("control", (name, False, command))

# Freezes the control program until the same program the originally called
# freeze calls unfreeze. When the control program is frozen, the freezing
# process can still send commands to it, but nothing else can.
def freeze(program):
  name = program.__class__.__name__
  program.write_to_feed("control", (name, "freeze"))

# Unfreezes the control program. If the control program has not been frozen by
# this program, it has no effect.
def unfreeze(program):
  name = program.__class__.__name__
  program.write_to_feed("control", (name, "unfreeze"))
