#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

#include "pruio_c_wrapper.h"
#include "pruio_pins.h"

// Step number for analog trigger.
#define STEP 11

int main(int argc, const char *argv[]) { 
  PruIo *io = pruio_new(0, 0x98, 0, 1);
  if (io->Errr) {
    printf("Initialization failed (%s)\n", io->Errr);
    return 1;
  }

  if (pruio_adc_step(io, STEP, 1, 0, 0, 0)) {
    printf("Failed setting trigger step: %s\n", io->Errr);
  }

  if (pruio_config(io, 1000, 0x4, 1e6, 4, 0)) {
    printf("Config failed (%s)\n", io->Errr); 
    return 1;
  }

  uint32_t trigger = pruio_mm_trg_ain(io, STEP, -15000, 0, 0);
  if (!trigger) {
    printf("Setting trigger failed: %s\n", io->Errr);
    return 1;
  }

  char *error = pruio_mm_start(io, trigger, 0, 0, 0);
  // Wait for trigger.
  if (error) {
    printf("Starting measurement failed: %s\n", error);
  } else {
    printf("Got trigger! Yay!\n");
  }

  pruio_destroy(io);

  return 0;
}
