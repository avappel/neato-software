#!/usr/bin/python

# Contains code for starting programs and coordinating them.

from multiprocessing import Pipe, Process

import os
import sys
import time

# A class representing a single program to be run on the robot as one process.
class Program:
  # Run the program.
  def __init__(self):
    # A list of all the pipes requested.
    self.pipe_names = []
    # A list of all the actual pipe objects.
    self.pipes = []

    # Run setup routine.
    self.setup()

  # Adds a new pipe to this particular process.
  def add_pipe(self, end):
    name = (self.__class__.__name__, end)
    if name not in self.pipe_names:
      self.pipe_names.append(name)

  # Adds a pipe object to this program. (Used by program dispatcher.)
  def add_pipe_object(self, pipe, name):
    exec("self." + name + " = pipe")
    self.pipes.append(pipe)

  # Perform any necessary setup for this program.
  def setup(self):
    # User can override this, but it's okay not to do anything.
    pass

  # Do whatever it is this program should do.
  def run(self):
    raise NotImplementedError("User must override this in all programs.")

if __name__ == "__main__":
  # Check in the programs directory and import everything.
  sys.path.append("programs")
  raw_names = os.listdir("programs")
  
  # Remove anything we can't import.
  names = []
  for name in raw_names:
    if name[-3:] == ".py":
      names.append(name.rstrip(".py"))

  # Instantiate each program.
  programs = []
  for program in names:
    exec("from %s import %s" % (program, program))
    exec("instance = " + program + "()")
    programs.append(instance)
  
  # Make all the requested pipes.
  for program in programs:
    for name in program.pipe_names:
      source, end = Pipe()
      program.add_pipe_object(source, name[1])

      # Get the other end of the pipe.
      other = None
      for other_program in programs:
        if other_program.__class__.__name__ == name[1]:
          other = other_program
      if not other:
        raise RuntimeError("Pipe endpoint '%s' is not a known program." % \
            (name[1]))

      other.add_pipe_object(end, name[0])

  # Set up and start all the processes for the programs.
  processes = []
  for program in programs:
    process = Process(target = program.run)
    process.start()
    processes.append(process)

  # Clean things up as they finish.
  while True:
    if not len(processes):  
      break

    to_delete = []
    for process in processes:
      if not process.is_alive():
        process.join()
        to_delete.append(process)
    for process in to_delete:
      processes.remove(process)

    time.sleep(1)
