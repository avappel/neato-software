#!/bin/bash

IP=$1
if [ -z "$IP" ]; then
  IP="10.8.0.10"
fi

NEATO="driver@${IP}"

# Send all the files to the Neato.
rsync -avz * ${NEATO}:neato

# Compile the C code.
ssh ${NEATO} "cd neato/c_src; ./build_c.sh; \
    find .. -name *.pyc | xargs rm &> /dev/null;"
