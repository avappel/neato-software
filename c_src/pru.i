/* Swig interface file for pru. */

%module pru

%{
#include <stdbool.h>
%}

void Cleanup();
bool Init();
int GetLeftDrop();
int GetRightDrop();
