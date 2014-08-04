// Reads data from the analog drop sensors very fast.

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>

#include "pruio_c_wrapper.h"
#include "pruio_pins.h"

// Analog inputs that are used for each sensor.
#define LEFT_AIN 1
#define RIGHT_AIN 2

static PruIo *io = NULL;

// Destroys PRU system.
void Cleanup() {
  pruio_destroy(io);
}

// Initializes PRU system.
bool Init() {
  io = pruio_new(0, 0x98, 0, 1);
  if (io->Errr) {
    printf("Initialization failed (%s)\n", io->Errr);
    return false;
  }

  if (pruio_config(io, 0, 0x1FE, 0, 4, 0)){
    printf("Config failed (%s)\n", io->Errr); 
    return false;
  }

  return true; 
}

// Gets a single reading from the analog sensors.
// The arguments are kind of funky here because SWIG works better with seperate
// inputs and outputs.
void GetDrops(int *left, int *right, int *right_out, int *left_out) { 
  *left = io->Value[LEFT_AIN + 1];
  *right = io->Value[RIGHT_AIN + 1];
  left_out = left;
  right_out = right;
}
