#!/bin/bash

NETLOGO_VERSION=6.1.1
NETLOGO_INSTALL_DIR="NetLogo $NETLOGO_VERSION"

if [ ! -d "$NETLOGO_INSTALL_DIR" ]; then
  wget https://ccl.northwestern.edu/netlogo/6.1.1/NetLogo-6.1.1-64.tgz
  tar xzf NetLogo-$NETLOGO_VERSION
else
  echo NetLogo $NETLOGO_VERSION already installed
fi

