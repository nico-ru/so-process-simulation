from typing import Dict
from flask.app import Flask
from flask.wrappers import Request
from flask import jsonify, request

from utils.util import get_url, log_request, send_service_call, log_runner, run_service
from lib.process import Activity, Process, ProcessRunner

billing = Flask("billing")


def run(request: Request):
    process = Process(
        [
            Activity("prepare invoice", attributes=dict(endpoint=request.path)),
            Activity(
                "send invoice",
                attributes=dict(endpoint=request.path),
                execution=send_invoice,
            ),
        ],
        header=["case_id", "activity", "timestamp", "endpoint"],
    )

    runner = ProcessRunner(process)
    runner.data["request"] = request
    runner.execute(case_id=request.headers.get("CORRELATION_ID", type=int))
    log_runner(runner, billing.name)


def send_invoice(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data)


@billing.route("/invoice", methods=["POST"])
def create_invoice():
    log_request(request, billing.name)
    run(request)
    return jsonify(success=True)


if __name__ == "__main__":
    run_service(billing)
