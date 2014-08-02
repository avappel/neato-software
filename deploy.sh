#!/bin/bash

NEATO="driver@10.8.0.10"

# Send all the files to the Neato.
rsync -avz * ${NEATO}:neato

# Compile the C code.
ssh ${NEATO} "cd neato/c_src; ./build_c.sh"
