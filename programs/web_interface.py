#!/usr/bin/python

# Implements a web interface for the robot.

from __future__ import division
from Queue import Empty

import json
import sys
sys.path.append("..")

from flask import Flask
from flask import render_template
from flask import request
from starter import Program

import motors
import log
import sensors

app = Flask(__name__)

@app.route("/")
def main():
  return render_template("main.html")

# Get battery percentage.
@app.route("/battery/")
def battery():
  analog = sensors.Analog(web_interface.root)
  voltage = analog.battery_voltage(stale_time = 60)
  percentage = voltage / 16000 * 100
  percentage = min(percentage, 100)
  return str(percentage)

# Determine whether we are charging or not.
@app.route("/charging/")
def charging():
  analog = sensors.Analog(web_interface.root)
  voltage = analog.charging(stale_time = 20)

  if int(voltage <= 20000):
    charging = 0
  else:
    charging = 1

  return str(charging)

# Get the latest logging messages. (JSON formatted.)
@app.route("/logging/")
def logging():
  # Get all the most recent messages.
  messages = []
  while True:
    try:
      messages.append(web_interface.root.web_logging.get(False))
    except Empty:
      break

  return json.dumps(messages)

# Determine whether lidar is active.
@app.route("/lds_active/", methods = ["GET", "POST"])
def lds_active():
  if request.method == "GET":
    return str(int(sensors.LDS.is_active(web_interface.root)))
  else:
    # Activate the LIDAR.
    if not web_interface.root.lds:
      web_interface.root.lds = sensors.LDS(web_interface.root)
    return str(1)

# Get a packet from the lidar.
@app.route("/lds/")
def lds():
  if web_interface.root.lds:
    packet = web_interface.root.lds.get_scan()
  else:
    packet = {}
  return json.dumps(packet)

# Instruct robot to drive forward.
@app.route("/drive_forward/", methods = ["POST"])
def drive_forward():
  # Activate wheels.
  if not web_interface.root.wheels:
    web_interface.root.wheels = motors.Wheels(web_interface.root);

  # Drive forward.
  web_interface.root.wheels.drive(100, 100, 300)
  return str(1)

@app.route("/stop/", methods = ["POST"])
def stop():
  if web_interface.root.wheels:
    web_interface.root.wheels.stop()

  return str(1)

class web_interface(Program):
  # The root instance of this class.
  root = None

  def setup(self):
    self.add_pipe("control")
    self.add_feed("web_logging")

  def run(self):
    web_interface.root = self
    self.lds = None
    self.wheels = None

    app.debug = True
    # The flask auto-reloader doesn't work well with multiprocessing.
    app.run(host = "0.0.0.0", use_reloader = False)
