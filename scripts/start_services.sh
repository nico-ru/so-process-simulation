#!/bin/bash

PYTHON=$(which python)
DIR=$(dirname ${BASH_SOURCE:-$0})
PID_FILE="$DIR/.services.pid"
SERVICES_PATH="$DIR/../services"

# clean up potentially still running services
/bin/bash "$DIR/stop_services.sh"

# start services
$PYTHON "$SERVICES_PATH/billing.py" > /dev/null 2>&1 &
billing_pid=$!
echo "started billing service (PID: $billing_pid)"

$PYTHON "$SERVICES_PATH/inventory.py" > /dev/null 2>&1 &
inventory_pid=$!
echo "started inventory service (PID: $inventory_pid)"

$PYTHON "$SERVICES_PATH/message.py" > /dev/null 2>&1 &
message_pid=$!
echo "started message service (PID: $message_pid)"

$PYTHON "$SERVICES_PATH/order.py" > /dev/null 2>&1 &
order_pid=$!
echo "started order service (PID: $order_pid)"

$PYTHON "$SERVICES_PATH/purchase.py" > /dev/null 2>&1 &
purchase_pid=$!
echo "started purchase service (PID: $purchase_pid)"

# save process ids to file
echo "$billing_pid $inventory_pid $message_pid $order_pid $purchase_pid" > $PID_FILE
