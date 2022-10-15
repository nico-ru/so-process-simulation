#!/bin/bash

DIR=$(dirname ${BASH_SOURCE:-$0})

/bin/bash "$DIR/start_services.sh"
/bin/bash "$DIR/start_simulation.sh"
