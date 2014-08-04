#!/bin/bash

GYP_GENERATORS=ninja gyp sensors.gyp \
    --toplevel-dir=`pwd` --depth=.. --no-circular-check
ninja -C out/Default/ all

# Move SWIGed libraries to their proper directories.
SWIG_DIR="../swig"

# Create directory.
if [ ! -d "$SWIG_DIR" ]; then
  mkdir "$SWIG_DIR"
else
  rm ${SWIG_DIR}/*
fi
echo "" > ${SWIG_DIR}/__init__.py

# Move files.
find out/Default/lib -name "libswig_*" -type f -exec cp -t $SWIG_DIR {} \+
find . -name "*.py" -type f -exec cp -t $SWIG_DIR {} \+

# Rename library files.
cd $SWIG_DIR
for f in *; do
  if [[ $f == libswig_*.so ]]; then
    mv $f _${f#libswig_}
  fi
done
