#!/bin/bash

PYTHON=$(which python)
DIR=$(dirname ${BASH_SOURCE:-$0})
PID_FILE="$DIR/.services.pid"
SERVICES_PATH="$DIR/.."
LOG_PATH="$DIR/../logs/server"

# clean up potentially still running services
/bin/bash "$DIR/stop_services.sh"

# start services
$PYTHON "$SERVICES_PATH/run_service.py" -s billing > "$LOG_PATH/billing.log" 2>&1 &
billing_pid=$!
echo "started billing service (PID: $billing_pid)"

$PYTHON "$SERVICES_PATH/run_service.py" -s inventory > "$LOG_PATH/inventory.log" 2>&1 &
inventory_pid=$!
echo "started inventory service (PID: $inventory_pid)"

$PYTHON "$SERVICES_PATH/run_service.py" -s message > "$LOG_PATH/message.log" 2>&1 &
message_pid=$!
echo "started message service (PID: $message_pid)"

$PYTHON "$SERVICES_PATH/run_service.py" -s order > "$LOG_PATH/order.log" 2>&1 &
order_pid=$!
echo "started order service (PID: $order_pid)"

$PYTHON "$SERVICES_PATH/run_service.py" -s purchase > "$LOG_PATH/purchase.log" 2>&1 &
purchase_pid=$!
echo "started purchase service (PID: $purchase_pid)"

# save process ids to file
echo "$billing_pid $inventory_pid $message_pid $order_pid $purchase_pid" > $PID_FILE
