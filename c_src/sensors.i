/* Swig interface file for sensors. */

%module sensors

%include "typemaps.i"

void Cleanup();
bool Init();
bool GetDrops(int *INPUT, int *INPUT, int *OUTPUT, int *OUTPUT);
