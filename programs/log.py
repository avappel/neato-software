# Logging system on the BBB.

import os
import sys
sys.path.append("..")

import time

from starter import Program

import robot_status

LOG_LOCATION = "../tmp/robot_logs/"

# Represents a logger writing to a single file.
class Logger:
  # Initial size of all the old logs.
  start_size = 0
  # Maximum space used by logs.
  max_size = 1000000000000

  def __init__(self, location):
    self.location = location
    self.file = None

    if not robot_status.is_testing():
      self.__remove_old()

      name = str(time.time()).split(".")[0]
      name += ".log"
      self.file_path = os.path.join(self.location, name)
      self.file = open(self.file_path, "w")

      # Set symlink.
      current = os.path.join(self.location, "current")
      if os.path.lexists(current):
        os.remove(current)
      os.symlink(name, current)

  # Remove old logs if things are getting too big.
  def __remove_old(self):
    old_files = os.listdir(self.location)
    old_files.sort()

    if "current" in old_files:
      old_files.remove("current")

    for i in range(0, len(old_files)):
      old_files[i] = os.path.join(self.location, old_files[i])

    size = sum(os.path.getsize(f) for f in old_files)

    while size > self.max_size:
      to_delete = old_files.pop(0)

      if (self.file != None and len(old_files) == 0):
        self.clear()
        Logger.start_size = 0
        return

      size -= os.path.getsize(to_delete)
      os.remove(to_delete)

    Logger.start_size = size

  def __del__(self):
    try:
      self.file.close()
    except AttributeError:
      pass

  # Write a log message to the file.
  def write(self, level, name, message):
    timestamp = time.ctime()
    self.file.write("[%s@%s] %s: %s\n" % (name, timestamp, level, message))

  # Flushes all messages not yet written.
  def flush(self):
    self.file.flush()

    # Clear the file if it's too big.
    if os.path.getsize(self.file_path) + self.start_size > self.max_size:
      self.__remove_old()

  # Clears the logfile.
  def clear(self):
    self.file.seek(0)
    self.file.truncate()

# Initialize root logging instance.
root = Logger(LOG_LOCATION)

class log(Program):
  def setup(self):
    self.add_feed("logging")

  def run(self):
    flush_pending = False

    while True:
      if (not flush_pending or not self.logging.empty()):
        level, name, message = self.logging.get()

        # Write it to the webserver, if it is running.
        try:
          if level != "DEBUG":
            self.write_to_feed("web_logging", (level, name, message), False)
        except (RuntimeError, ValueError):
          # It's not critical that we write it.
          pass

        root.write(level, name, message)
        flush_pending = True

      else:
        root.flush()
        flush_pending = False

# Shortcuts for logging to the root logger at specific levels.
if robot_status.is_testing():
  def __log_write(level, message):
    print "%s: %s" % (level, message)
else:
  def __log_write(level, message):
    program = robot_status.program
    name = program.__class__.__name__
    Program.write_to_feed("logging", (level, name, message))

def debug(message):
  __log_write("DEBUG", message)

def info(message):
  __log_write("INFO", message)

def warning(message):
  __log_write("WARNING", message)

def error(message):
  __log_write("ERROR", message)

def fatal(message):
  __log_write("FATAL", message)

  # Exit with failure.
  sys.exit(1)
