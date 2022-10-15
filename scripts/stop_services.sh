#!/bin/bash

DIR=$(dirname ${BASH_SOURCE:-$0})
PID_FILE="$DIR/.services.pid"

if [ -f "$PID_FILE" ]; then
    kill -9 $(<"$PID_FILE")
    rm $PID_FILE
fi
