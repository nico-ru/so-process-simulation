from flask import jsonify, request
from flask.app import Flask

from utils.util import log_request, run_service

message = Flask("message")


@message.route("/common", methods=["POST"])
def create_invoice():
    log_request(request, message.name)
    return jsonify(success=True)


if __name__ == "__main__":
    run_service(message)
