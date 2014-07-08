#!/usr/bin/python

# Implements a web interface for the robot.

from __future__ import division

import sys
sys.path.append("..")

import json

from flask import Flask
from flask import render_template
from starter import Program

import log
import sensors

app = Flask(__name__)

@app.route("/")
def main():
  return render_template("main.html")

# Get battery percentage.
@app.route("/battery/")
def battery():
  voltage = web_interface.analog.battery_voltage(stale_time = 60)
  percentage = voltage / 16000 * 100
  return str(percentage)

# Get the latest logging messages. (JSON formatted.)
@app.route("/logging/")
def logging():
  # Get all the most recent messages.
  messages = []
  while not web_interface.logging.empty():
    messages.append(web_interface.logging.get(False))

  return json.dumps(messages)

class web_interface(Program):
  # These get used by the route handlers.
  analog = None
  logging = None

  def setup(self):
    self.add_pipe("control")
    self.add_feed("web_logging")

  def run(self):
    web_interface.analog = sensors.Analog(self)
    web_interface.logging = self.web_logging

    app.debug = True
    # The flask auto-reloader doesn't work well with multiprocessing.
    app.run(host = "0.0.0.0", use_reloader = False)
