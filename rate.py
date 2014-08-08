import time

# When one call is made every loop iteration, it insures that each iteration
# takes exactly this many seconds.
class Rate():
  def __init__(self):
    self.last_time  = 0
  def rate(self, interval):
    elapsed = time.time() - self.last_time
    self.last_time = time.time()

    if elapsed > interval:
      return
    else:
      remaining = interval - elapsed
      time.sleep(remaining)
      return
