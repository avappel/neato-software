# General system functions as well as code for interfacing with the serial API.

import sys
sys.path.append("..")

import serial

from starter import Program

import log
import rate

class control(Program):
  def setup(self):
    self.add_feed("control")

  def run(self):
    self.serial = serial.Serial(port = "/dev/ttyACM0")
    # Enable test mode on the neato.
    self.serial.write("testmode on\n")

    freezing_program = None

    while True:
      # Check for commands from all our pipes.
      data = self.control.get()
      source = data[0]
      
      if len(data) == 3:
        if (not freezing_program or source == freezing_program):
          # Normal command.
          output = data[1]
          command = data[2]
          log.debug(self, "Command: %s" % (command))

          if output:
            # We need to send the output back.
            data = self.__get_output(command)
            pipe = getattr(self, source)
            pipe.send(data)
          else:
            # No need to send the output.
            self.__send_command(command)
      
      else:
        # Other command.
        if (data[1] == "freeze" and not freezing_program):
          log.info(self, "Freezing control program.")
          freezing_program = source
        elif (data[1] == "unfreeze" and pipe == freezing_pipe):
          log.info(self, "Unfreezing control program.")
          freezing_program = None

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
