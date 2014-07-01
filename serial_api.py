# Versions of API interface functions for use by the user. The first argument is
# a program subclass instance.

def get_output(program, command):
  program.control.send((True, command))
  return program.control.recv()

def send_command(program, command):
  program.control.send((False, command))
