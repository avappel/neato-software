#!/usr/bin/python

# Contains code for starting programs and coordinating them.

from multiprocessing import Pipe, Process, Queue, Array
from Queue import Full

import atexit
import os
import sys
import time

from swig import pru

import robot_status

# A class representing a single program to be run on the robot as one process.
class Program:
  def __init__(self):
    # A list of all the pipes requested.
    self.pipe_names = []
    # A list of all the actual pipe objects.
    self.pipes = []
    # A list of the feeds that we requested.
    self.feed_names = []
    # A list of feeds we own.
    self.feeds = []
    # A dictionary of all the feeds we can write to.
    self.write_feeds = {}

    # Run setup routine.
    self.setup()

  # Verify that this name is not already in use.
  def __check_name_collisions(self, name):
    in_use = False
    
    if name in self.pipe_names:
      in_use = True
    if name in self.feed_names:
      in_use = True

    if in_use:
      raise ValueError("Name '%s' is already in use." % (name))

  # Adds a new pipe to this particular process.
  def add_pipe(self, end):
    name = (self.__class__.__name__, end)
    self.__check_name_collisions(name)

    self.pipe_names.append(name)

  # Adds a new feed owned by this process.
  def add_feed(self, name):
    self.__check_name_collisions(name)
    self.feed_names.append(name)

  # Adds a pipe object to this program. (Used by program dispatcher.)
  def add_pipe_object(self, pipe, name):
    exec("self." + name + " = pipe")
    self.pipes.append(pipe)

  def add_feed_object(self, queue, name):
    exec("self." + name + " = queue")
    self.feeds.append(queue)

  # Allows a subclass to write to a named feed.
  def write_to_feed(self, name, message, block = True):
    try:
      feed = self.write_feeds[name]
    except KeyError:
      raise ValueError("No feed with name '%s' exists." % (name))

    try:
      feed.put(message, block)
    except Full:
      raise RuntimeError("Write would block.")

  # Perform any necessary setup for this program.
  def setup(self):
    # User can override this, but it's okay not to do anything.
    pass

  # Do whatever it is this program should do.
  def run(self):
    raise NotImplementedError("User must override this in all programs.")

if __name__ == "__main__":
  # Cleanup pru when everything is done.
  atexit.register(pru.Cleanup)

  # Check in the programs directory and import everything.
  sys.path.append("programs")
  raw_names = os.listdir("programs")

  raw_names.remove("__init__.py")
  
  # Remove anything we can't import.
  names = []
  for name in raw_names:
    if name[-3:] == ".py":
      names.append(name[:-3])

  # Instantiate each program.
  programs = []
  for program in names:
    exec("from %s import %s" % (program, program))
    exec("instance = " + program + "()")
    programs.append(instance)

  # Create underlying shared memory array for robot status.
  status_array = Array('i', robot_status.array_size)
  for program in programs:
    program.status_array = status_array
  
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
        raise ValueError("Pipe endpoint '%s' is not a known program." % \
            (name[1]))

      other.add_pipe_object(end, name[0])

  # Set up the necessary feed systems.
  for program in programs:
    for name in program.feed_names:
      queue = Queue()

      for other_program in programs:
        if (other_program != program and name not in other_program.write_feeds):
          other_program.write_feeds[name] = queue

      program.add_feed_object(queue, name)

  # Set up and start all the processes for the programs.
  processes = {}
  for program in programs:
    process = Process(target = program.run)
    process.start()
    processes[process] = program.run

  # Clean things up as they finish, or restart them if they fail.
  while True:
    if not len(processes.keys()):  
      break

    to_delete = []
    for process in processes.keys():
      if not process.is_alive():
        process.join()

        if process.exitcode:
          # Process failed.
          new_process = Process(target = processes[process])
          new_process.start()
          processes[new_process] = processes[process]

        to_delete.append(process)
    for process in to_delete:
      processes.pop(process, None)

    time.sleep(1)
