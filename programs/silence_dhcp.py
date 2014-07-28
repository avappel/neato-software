# A hack to make it kill the rogue DHCP server on the WNCE2001 if it starts.

import subprocess
import sys
import time
sys.path.append("..")

from starter import Program

import log
import neato_system

class silence_dhcp(Program):
  wnce_addr = "10.15.2.177"

  def run(self):
    while True:
      # Check for dhcping.
      output = subprocess.check_output("which dhcping", shell = True)
      if not output:
        log.fatal(self, "dhcping not found.")

      try:
        output = subprocess.check_output("dhcping %s" % (self.wnce_addr),
            shell = True, stderr = subprocess.STDOUT)
      except subprocess.CalledProcessError as e:
        output = str(e.output)

      lines = output.split("\n")
      responses = []
      for line in lines:
        if "Got answer from:" in line:
          response_addr = line.split(": ")[1]
          responses.append(response_addr)
          
          log.info(self, "Got dhcp response from %s." % (response_addr))

      # If it somehow gets reset, the second address will be the one it has.
      bad_addrs = [self.wnce_addr, "192.168.1.251"]
      for addr in bad_addrs:
        if addr in responses:
          log.error("WNCE IS RUNNING ROGUE DHCP SERVER!")
          
          # Hibernating will automatically cut power to the wnce. It will,
          # however, also interrupt power to us.
          neato_system.hibernate()

      time.sleep(60)
