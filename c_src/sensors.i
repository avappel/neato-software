/* Swig interface file for sensors. */

%module sensors

%{
#include <stdbool.h>
%}

void Cleanup();
bool Init();
int GetLeftDrop();
int GetRightDrop();
