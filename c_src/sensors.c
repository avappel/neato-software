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
void GetDrops(uint16_t *left, uint16_t *right) { 
  *left = io->Value[LEFT_AIN + 1];
  *right = io->Value[RIGHT_AIN + 1];
}

int main(int argc, const char **argv) {
  Init();

  uint16_t left;
  uint16_t right;
  GetDrops(&left, &right);
  printf("Drop sensors: %d, %d\n", left, right);
  sleep(1);
  GetDrops(&left, &right);
  printf("Drop sensors: %d, %d\n", left, right);

  Cleanup();
}
