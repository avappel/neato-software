#!/bin/bash

GYP_GENERATORS=ninja gyp sensors.gyp \
    --toplevel-dir=`pwd` --depth=.. --no-circular-check
ninja -C out/Default/ all
