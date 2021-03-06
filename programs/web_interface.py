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

import continuous_driving
import log
import sensors
import watchdog

app = Flask(__name__)

@app.route("/")
def main():
  return render_template("main.html")

# Get battery percentage.
@app.route("/battery/")
def battery():
  analog = sensors.Analog()
  voltage = analog.battery_voltage(stale_time = 60)
  percentage = voltage / 16000 * 100
  percentage = min(percentage, 100)
  return str(percentage)

# Determine whether we are charging or not.
@app.route("/charging/")
def charging():
  analog = sensors.Analog()
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
    status = int(sensors.LDS.is_active())

    # If it's active, let's make an instance of it.
    if (status and not web_interface.root.lds):
      web_interface.root.lds = sensors.LDS()
    # If it's not active, be sure we don't have one.
    if (not status and web_interface.root.lds):
      web_interface.root.lds = None

    return str(status)
  else:
    # Activate the LIDAR.
    if not web_interface.root.lds:
      web_interface.root.lds = sensors.LDS()
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
  # Drive forward.
  continuous_driving.drive(web_interface.root, 1, 1, 300)
  web_interface.root.quickturn = False
  return str(1)

@app.route("/drive_backward/", methods = ["POST"])
def drive_backward():
  # Drive backward.
  continuous_driving.drive(web_interface.root, -1, -1, 300)
  web_interface.root.quickturn = False
  return str(1)

@app.route("/turn_left/", methods = ["POST"])
def turn_left():
  if web_interface.root.quickturn:
    # Quickturn.
    continuous_driving.drive(web_interface.root, -1, 1, 100)
  else:
    continuous_driving.drive(web_interface.root, 0, 1, 300)
    # Next time we get a request, it must be because the driver released the up
    # or down arrow.
    web_interface.root.quickturn = True

  return str(1)

@app.route("/turn_right/", methods = ["POST"])
def turn_right():
  if web_interface.root.quickturn:
    continuous_driving.drive(web_interface.root, 1, -1, 100)
  else:
    continuous_driving.drive(web_interface.root, 1, 0, 300)
    web_interface.root.quickturn = True

  return str(1)

@app.route("/stop/", methods = ["POST"])
def stop():
  # Stop moving.
  continuous_driving.stop(web_interface.root)
  web_interface.root.quickturn = True
  return str(1)

# Callback for the watchdog.
def callback(program):
  continuous_driving.stop(program)

# Feeds the watchdog on the wheels.
@app.route("/feed_watchdog/", methods = ["POST"])
def feed_watchdog():
  # Register the watchdog if we haven't already.
  if not web_interface.root.has_watchdog:
    watchdog.register(web_interface.root, 5, callback)
    web_interface.root.has_watchdog = True
    # If we're reconnecting, we probably want the quickturn to start. (It did
    # not get set if the watchdog timed out.)
    web_interface.root.quickturn = True
    log.debug("Fed watchdog.")

  watchdog.feed(web_interface.root)
  return str(1)

# Deregisters the watchdog.
@app.route("/stop_watchdog/", methods = ["POST"])
def stop_watchdog():
  if web_interface.root.has_watchdog:
    watchdog.deregister(web_interface.root)
    web_interface.root.has_watchdog = False

  return str(1)

class web_interface(Program):
  # The root instance of this class.
  root = None

  def setup(self):
    self.add_pipe("control")
    self.add_pipe("watchdog")

    self.add_feed("web_logging")

  def run(self):
    web_interface.root = self
    self.lds = None
    self.quickturn = True
    self.has_watchdog = False

    app.debug = True
    # The flask auto-reloader doesn't work well with multiprocessing.
    app.run(host = "0.0.0.0", use_reloader = False)
