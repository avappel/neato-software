# General system functions as well as code for interfacing with the serial API.

import sys
sys.path.append("..")

import serial
import time

from starter import Program

import log
import rate

# A simple memmory cache.
class Cache:
  # Time in seconds before entries go stale.
  stale_time = 5

  def __init__(self):
    # The actual cached data, indexed by command
    self.data = {}
    # Cached timestamps, indexed by command.
    self.timestamps = {}
    # We also save the names of programs that requests came from.
    self.sources = {}

  # If there is valid item, return it, otherwise, return None.
  def get_item(self, command, source, stale_time = None):
    if command not in self.data.keys():
      return None

    data_source = self.sources[command]
    if data_source == source:
      # If the same program is running the same command, it's probably because
      # they want new data.
      return None

    data = self.data[command]

    if stale_time == None:
      stale = Cache.stale_time
    else:
      stale = stale_time
    
    timestamp = self.timestamps[command]
    if time.time() - timestamp >= stale:
      return None

    return data

  # Add a new item to the cache, or update an existing one.
  def add(self, command, data, source):
    self.data[command] = data
    self.timestamps[command] = time.time()
    self.sources[command] = source

class control(Program):
  def setup(self):
    self.add_feed("control")

  def run(self):
    self.serial = serial.Serial(port = "/dev/ttyACM0")
    # Enable test mode on the neato.
    self.serial.write("testmode on\n")

    self.cache = Cache()
    freezing_program = None

    while True:
      # Check for commands from all our pipes.
      data = self.control.get()
      source = data.Source
  
      # Freeze or unfreeze.
      if (data.Command == "freeze" and not freezing_program):
        log.info(self, "Freezing control program.")
        freezing_program = source
      elif (data.Command == "unfreeze" and source == freezing_program):
        log.info(self, "Unfreezing control program.")
        freezing_program = None

      # Normal serial command.
      else:
        if (not freezing_program or source == freezing_program):
          output = data.Output
          command = data.Command
          stale = data.Stale
          log.debug(self, "Command: %s" % (command))

          if output:
            # We need to send the output back.
            result = self.cache.get_item(command, source, stale_time = stale)
            if not result:
              result = self.__get_output(command)
              self.cache.add(command, result, source)
            else:
              log.debug(self, "Cache hit on %s." % \
                  (command))

            pipe = getattr(self, source)
            pipe.send(result)
          else:
            # No need to send the output.
            self.__send_command(command)
      
  # Gets results from a command on the neato.
  def __get_output(self, command):
    self.serial.flush()
    self.__send_command(command)

    response = ""
    start = False
    while True:
      try:
        data = self.serial.read(self.serial.inWaiting())
      except (OSError, serial.SerialException):
        # No data to read.
        log.warning(self, "Got no serial data. Retrying...")
        continue

      if start:
        response += data

      if command in data:
        # Remove everything up to the command.
        data = data.split(command)
        data = data[1]

        start = True

      # All responses end with this character.
      if (response != "" and response[-1] == ""):
        # Get rid of end character and newline.
        response = response[:-2]

        # All responses are CSVs, so we can turn them into a nice little dict.
        lines = response.split("\n")
        ret = {}
        for line in lines:
          line = line.rstrip("\r")
          split = line.split(",")
          if len(split) > 2:
            ret[split[0]] = split[1:]
          elif len(split) == 2:
            ret[split[0]] = split[1]
          else:
            ret[split[0]] = None

        log.debug(self, "Got response: %s" % (str(ret)))
        return ret

  # Sends a command to the neato.
  def __send_command(self, command):
    self.serial.write(command + "\n")
