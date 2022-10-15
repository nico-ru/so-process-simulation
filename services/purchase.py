from typing import Dict
from flask.app import Flask
from flask.wrappers import Request
from flask import jsonify, request

from utils.util import get_url, log_request, log_runner, send_service_call, run_service
from lib.process import Activity, Process, ProcessRunner

purchase = Flask("purchase")


def run(request: Request):
    process = Process(
        [
            Activity("reorder inventory", attributes=dict(endpoint=request.path)),
            Activity(
                "inform about restock",
                attributes=dict(endpoint=request.path),
                execution=inform_about_restock,
            ),
        ],
        header=["case_id", "activity", "timestamp", "endpoint"],
    )

    runner = ProcessRunner(process)
    runner.data["request"] = request
    runner.execute(case_id=request.headers.get("CORRELATION_ID", type=int))
    log_runner(runner, purchase.name)


def inform_about_restock(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data)


@purchase.route("/purchase", methods=["POST"])
def create_invoice():
    log_request(request, purchase.name)
    run(request)
    return jsonify(success=True)


if __name__ == "__main__":
    run_service(purchase)
