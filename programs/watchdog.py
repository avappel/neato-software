# A safety feature that can disable certain systems in the event of a lost
# connection or such.

import sys
import time
sys.path.append("..")

from starter import Program

import log
import rate

class watchdog(Program):
  def setup(self):
    self.add_feed("watchdog_jobs")

  def run(self):
    jobs = []
    timed_out = []
    last_feeds = {}
    timeouts = {}
    callbacks = {}
    while True:
      rate.rate(1)

      # Check for new jobs.
      new_jobs = []
      if not jobs:
        # Block until we get a job if we don't have any.
        new_jobs = [self.watchdog_jobs.get()]
      while not self.watchdog_jobs.empty():
        new_jobs.append(self.watchdog_jobs.get())

      for job in new_jobs:
        name = job[0]
        if job[1] == "register":
          timeouts[name] = job[2]
          callbacks[name] = job[3]
          jobs.append(name)

          log.info("Got new job: %s" % (name))
        else:
          try:
            jobs.remove(name)
          except ValueError:
            raise ValueError("No watchdog '%s' registered." % (name))

          timeouts.pop(name, None)
          callbacks.pop(name, None)

          if name in last_feeds.keys():
            last_feeds.pop(name, None)

          log.info("Removed job: %s" % (name))

      # Get any new feed events.
      for name in jobs:
        pipe = getattr(self, name)

        if pipe.poll():
          timestamp = pipe.recv()
          log.debug("Got feed from %s at %f." % (name, timestamp))
          last_feeds[name] = timestamp

          if name in timed_out:
            timed_out.remove(name)

      # Check to see if anything must be disabled.
      for key in last_feeds.keys():
        if time.time() - last_feeds[key] >= timeouts[key]:
          if key not in timed_out:
            log.error("Timeout on %s." % (key))
            # Run callback.
            callbacks[name](self)

            timed_out.append(key)

# Registers a new watchdog.
def register(program, timeout, callback):
  name = program.__class__.__name__
  program.write_to_feed("watchdog_jobs", (name, "register", timeout, callback))

# Deregisters an existing watchdog.
def deregister(program):
  name = program.__class__.__name__
  program.write_to_feed("watchdog_jobs", (name, "deregister"))

# Feeds the watchdog.
def feed(program):
  program.watchdog.send(time.time())
