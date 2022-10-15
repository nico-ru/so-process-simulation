import random
from typing import Dict
from flask.app import Flask
from flask.wrappers import Request
from flask import jsonify, request

from utils.util import get_url, log_request, log_runner, send_service_call, run_service
from lib.process import Activity, Process, Decision, ProcessRunner

inventory = Flask("inventory")


def run(request: Request):
    process = Process(
        [
            Activity(
                "check inverntory",
                attributes=dict(endpoint=request.path),
                execution=check_inventory,
            ),
            Decision(
                [
                    Activity(),
                    Activity(
                        "request reorder",
                        attributes=dict(endpoint=request.path),
                        execution=request_reorder,
                    ),
                ],
                condition=lambda data: 1
                if len(data["unavailable_products"]) > 0
                else 0,
            ),
            Activity(
                "send confirmation",
                attributes=dict(endpoint=request.path),
                execution=send_confirmation,
            ),
        ],
        header=["case_id", "activity", "timestamp", "endpoint"],
    )

    runner = ProcessRunner(process)
    runner.data["request"] = request
    runner.execute(case_id=request.headers.get("CORRELATION_ID", type=int))
    log_runner(runner, inventory.name)


def check_inventory(data: Dict):
    data["unavailable_products"] = []
    for product in data["request"].get_json():
        available = random.randint(0, 100) > 10
        if not available:
            data["unavailable_products"].append(product)


def request_reorder(data: Dict):
    to = get_url("purchase")
    send_service_call(to, data)


def send_confirmation(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data)


@inventory.route("/inventory", methods=["POST"])
def create_invoice():
    log_request(request, inventory.name)
    run(request)
    return jsonify(success=True)


if __name__ == "__main__":
    run_service(inventory)
