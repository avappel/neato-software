# Versions of API interface functions for use by the user. The first argument is
# a program subclass instance.

# Get the output of a command.
def get_output(program, command):
  program.control.send((True, command))
  return program.control.recv()

# Run a command without output.
def send_command(program, command):
  program.control.send((False, command))

# Freezes the control program until the same program the originally called
# freeze calls unfreeze. When the control program is frozen, the freezing
# process can still send commands to it, but nothing else can.
def freeze(program):
  program.control.send("freeze")

# Unfreezes the control program. If the control program has not been frozen by
# this program, it has no effect.
def unfreeze(program):
  program.control.send("unfreeze")
