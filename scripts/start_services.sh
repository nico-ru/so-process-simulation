#!/bin/bash

PYTHON=$(which python)
DIR=$(dirname ${BASH_SOURCE:-$0})
PID_FILE="$DIR/.services.pid"
SERVICES_PATH="$DIR/../services"
LOG_PATH="$DIR/../logs/server"

# clean up potentially still running services
/bin/bash "$DIR/stop_services.sh"

# start services
$PYTHON "$SERVICES_PATH/billing.py" > "$LOG_PATH/billing.log" 2>&1 &
billing_pid=$!
echo "started billing service (PID: $billing_pid)"

$PYTHON "$SERVICES_PATH/inventory.py" > "$LOG_PATH/inventory.log" 2>&1 &
inventory_pid=$!
echo "started inventory service (PID: $inventory_pid)"

$PYTHON "$SERVICES_PATH/message.py" > "$LOG_PATH/message.log" 2>&1 &
message_pid=$!
echo "started message service (PID: $message_pid)"

$PYTHON "$SERVICES_PATH/order.py" > "$LOG_PATH/order.log" 2>&1 &
order_pid=$!
echo "started order service (PID: $order_pid)"

$PYTHON "$SERVICES_PATH/purchase.py" > "$LOG_PATH/purchase.log" 2>&1 &
purchase_pid=$!
echo "started purchase service (PID: $purchase_pid)"

# save process ids to file
echo "$billing_pid $inventory_pid $message_pid $order_pid $purchase_pid" > $PID_FILE
