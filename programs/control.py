# General system functions as well as code for interfacing with the serial API.

import sys
sys.path.append("..")

import serial

from starter import Program

import log
import rate

class control(Program):
  def run(self):
    self.serial = serial.Serial(port = "/dev/ttyACM0", timeout = 0)
    # Enable test mode on the neato.
    self.serial.write("testmode on\n")

    freezing_pipe = None

    while True:
      # TODO (danielp): Change this to a feed-based system with pipes used only
      # for the output.
      rate.rate(0.005)
      
      # Check for commands from all our pipes.
      for pipe in self.pipes:
        if pipe.poll():
          data = pipe.recv()
          
          if type(data) == tuple:
            if (not freezing_pipe or pipe == freezing_pipe):
              # Normal command.
              output = data[0]
              command = data[1]
              log.debug("Command: %s" % (command))

              if output:
                # We need to send the output back.
                data = self.__get_output(command)
                pipe.send(data)
              else:
                # No need to send the output.
                self.__send_command(command)

          else:
            # Other command.
            if (data == "freeze" and not freezing_pipe):
              log.info(self, "Freezing control program.")
              freezing_pipe = pipe
            elif (data == "unfreeze" and pipe == freezing_pipe):
              log.info(self, "Unfreezing control program.")
              freezing_pipe = None

  # Gets results from a command on the neato.
  def __get_output(self, command):
    self.serial.flushInput()
    self.__send_command(command)

    response = ""
    start = False
    while True:
      line = self.serial.read(1024)
      if start:
        response += line

      if command in line:
        start = True

      # All responses end with this character.
      if (response != "" and response[-1] == ""):
        # Get rid of end character and newline.
        response = response[:-2]

        # All responses are CSVs, so we can turn them into a nice little dict.
        lines = response.split("\r\n")
        ret = {}
        for line in lines:
          split = line.split(",")
          if len(split) > 2:
            ret[split[0]] = split[1:]
          elif len(split) == 2:
            ret[split[0]] = split[1]
          else:
            ret[split[0]] = None

        return ret

  # Sends a command to the neato.
  def __send_command(self, command):
    self.serial.write(command + "\n")
