# Logging system on the BBB.

import sys
sys.path.append("..")

import time

from starter import Program

LOG_LOCATION = "/home/driver/test_log.log"

# Represents a logger writing to a single file.
class Logger:
  def __init__(self, location):
    self.file = open(location, "w")
  
  def __del__(self):
    self.file.close()

  # Write a log message to the file.
  def write(self, level, name, message):
    timestamp = time.ctime()
    self.file.write("[%s@%s] %s: %s\n" % (name, timestamp, level, message))

    # If it's fatal, we abort with an error.
    if level == "FATAL":
      self.file.close()
      sys.exit(1)
  
  # Flushes all messages not yet written.
  def flush(self):
    self.file.flush()

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
def __log_write(level, program, message):
  name = program.__class__.__name__
  program.write_to_feed("logging", (level, name, message))

def debug(program, message):
  __log_write("DEBUG", program, message)

def info(program, message):
  __log_write("INFO", program, message)

def warning(program, message):
  __log_write("WARNING", program, message)

def error(program, message):
  __log_write("ERROR", program, message)

def fatal(program, message):
  __log_write("FATAL", program, message)
  
  # Exit with failure.
  sys.exit(1)
