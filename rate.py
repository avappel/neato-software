import time

last_time = time.time()

# When one call is made every loop iteration, it insures that each iteration
# takes exactly this many seconds.
def rate(interval):
  global last_time
  elapsed = time.time() - last_time
  last_time = time.time()

  if elapsed > interval:
    return
  else:
    remaining = interval - elapsed
    time.sleep(remaining)
    return
