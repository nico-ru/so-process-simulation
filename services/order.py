from typing import Dict
from flask.app import Flask
from flask.wrappers import Request
from flask import jsonify, request

from utils.util import get_url, log_request, log_runner, send_service_call, run_service
from lib.process import Process, Activity, Decision, Sequence, ProcessRunner

order = Flask("order")


def run(request: Request):
    process = Process(
        [
            Activity("analyze request", attributes=dict(endpoint=request.path)),
            Activity(
                "check availability",
                attributes=dict(endpoint=request.path),
                execution=check_availability,
            ),
            Activity(
                "receive information",
                attributes=dict(endpoint=request.path),
                execution=receive_information,
            ),
            Decision(
                [
                    Sequence(
                        [
                            Activity(
                                "request invoice",
                                attributes=dict(endpoint=request.path),
                                execution=reqeust_invoice,
                            ),
                            Activity(
                                "confirm order",
                                attributes=dict(endpoint=request.path),
                                execution=confirm_order,
                            ),
                        ]
                    ),
                    Activity(
                        "reject order",
                        attributes=dict(endpoint=request.path),
                        execution=reject_order,
                    ),
                ],
                [60, 40],
            ),
        ],
        header=["case_id", "activity", "timestamp", "endpoint"],
    )
    runner = ProcessRunner(process)
    runner.data["request"] = request
    runner.execute(case_id=request.headers.get("CORRELATION_ID", type=int))
    log_runner(runner, order.name)


def check_availability(data: Dict):
    to = get_url("inventory", "inventory")
    send_service_call(to, data)


def receive_information(data: Dict):
    pass


def reqeust_invoice(data: Dict):
    to = get_url("billing", "invoice")
    send_service_call(to, data)


def confirm_order(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data)


def reject_order(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data)


@order.route("/order", methods=["POST"])
def create_order():
    log_request(request, order.name)
    run(request)
    return jsonify(success=True)


if __name__ == "__main__":
    run_service(order)
