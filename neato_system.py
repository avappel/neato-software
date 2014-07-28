# Collection of general commands for the neato.

import serial_api

def shutdown():
  serial_api.send_command("SetSystemMode Shutdown")

def hibernate():
  serial_api.send_command("SetSystemMode Hibernate")
