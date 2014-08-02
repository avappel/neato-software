// Reads data from the analog drop sensors very fast.

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

#include "pruio_c_wrapper.h"
#include "pruio_pins.h"

// Analog inputs for each drop sensor.
#define LEFT_AIN 1
#define RIGHT_AIN 2
// Step numbers for analog triggers.
#define LEFT_STEP 11
#define RIGHT_STEP 12
// Thresholds at which point each sensor reading is considered abnormal.
#define LEFT_THRESH 25000
#define RIGHT_THRESH 25000

// Blocks until a drop sensor has an abnormal reading.
bool WaitForDrop() { 
  PruIo *io = pruio_new(0, 0x98, 0, 1);
  if (io->Errr) {
    printf("Initialization failed (%s)\n", io->Errr);
    return false;
  }

  // Configure steps.
  if (pruio_adc_step(io, LEFT_STEP, LEFT_AIN, 0, 0, 0)) {
    printf("Failed setting left trigger step: %s\n", io->Errr);
    return false;
  }
  if (pruio_adc_step(io, RIGHT_STEP, RIGHT_AIN, 0, 0, 0)) {
    printf("Failed setting right trigger step: %s\n", io->Errr);
    return false;
  }

  uint8_t step_mask = (1 << (LEFT_AIN + 1)) + (1 << (RIGHT_AIN + 1));
  if (pruio_config(io, 10, step_mask, 1e6, 4, 0)) {
    printf("Config failed (%s)\n", io->Errr); 
    return false;
  }

  // Make triggers for each sensor.
  uint32_t left_trigger = pruio_mm_trg_ain(io, LEFT_STEP, -LEFT_THRESH, 0, 0);
  if (!left_trigger) {
    printf("Setting left trigger failed: %s\n", io->Errr);
    return false;
  }
  uint32_t right_trigger =
      pruio_mm_trg_ain(io, RIGHT_STEP, -RIGHT_THRESH, 0, 0);
  if (!right_trigger) {
    printf("Setting right trigger failed: %s\n", io->Errr);
    return false;
  }

  // Wait for triggers.
  char *error = pruio_mm_start(io, left_trigger, right_trigger, 0, 0);
  if (error) {
    printf("Starting measurement failed: %s\n", error);
  }

  pruio_destroy(io);

  return true;
}

int main(int argc, const char **argv) {
  WaitForDrop();
  printf("Got drop.\n");
}
