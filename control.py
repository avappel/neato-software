# General system functions as well as code for interfacing with the serial API.

import serial

stream = serial.Serial(port = "/dev/ttyACM0", timeout = 0)

# Enable test mode on the neato.
stream.write("testmode on\n")

# Gets results from a command on the neato.
def get_output(command):
  stream.flushInput()
  send_command(command)

  response = ""
  start = False
  while True:
    line = stream.read(1024)
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
        else:
          ret[split[0]] = split[1]

      return ret

# Sends a command to the neato.
def send_command(command):
  stream.write(command + "\n")

# Shutdown the robot. (NOTE: This will kill power to the control system.)
def shutdown():
  send_command("SetSystemMode Shutdown")

# Put the robot on standby.
def standby():
  send_command("SetSystemMode Standby")
