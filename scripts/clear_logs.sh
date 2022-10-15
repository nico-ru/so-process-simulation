#!/bin/bash

DIR=$(dirname ${BASH_SOURCE:-$0})
SERVICES="$DIR/../logs/services/*/logs"

if [ -n "$1" ]
then
    SERVICES=""
    for var in "$@"
    do 
        SERVICES+="services/$var/logs "
    done
fi

DEL_FILES=$(/usr/bin/find $SERVICES -type f -name "*.log.*")
if [ ! -z "$DEL_FILES" ]; then
    echo "$DEL_FILES"
    read -p "do you want to delete these files? ([y]/n) " -n 1 -r
    echo    # move to a new line
    if [[ ! $REPLY =~ ^[Nn]$ ]]
    then
        /usr/bin/find $SERVICES -type f -name "*.log.*" -exec rm {} \;
    fi
else
    echo "nothing to delete"
fi
