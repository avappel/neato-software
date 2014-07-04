#!/usr/bin/python

# Implements a web interface for the robot.

from __future__ import division

import sys
sys.path.append("..")

from flask import Flask
from flask import render_template
from starter import Program

import sensors

app = Flask(__name__)

@app.route("/")
def main():
  return render_template("main.html")

# Get battery percentage.
@app.route("/battery/")
def battery():
  voltage = web_interface.analog.battery_voltage()
  percentage = voltage / 16000 * 100
  return str(percentage)

class web_interface(Program):
  # These get used by the route handlers.
  analog = None

  def setup(self):
    self.add_pipe("control")
  
  def run(self):
    web_interface.analog = sensors.Analog(self)

    app.debug = True
    # The flask auto-reloader doesn't work well with multiprocessing.
    app.run(host = "0.0.0.0", use_reloader = False)
