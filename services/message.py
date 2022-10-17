import dotenv
from flask import jsonify, request
from flask.app import Flask

from utils.util import log_request
from utils.service import run_service, configure_service

dotenv.load_dotenv()

message = Flask("message")


@message.route("/common", methods=["POST"])
def create_invoice():
    log_request(request, message.name)
    return jsonify(success=True)


if __name__ == "__main__":
    configure_service(message)
    run_service(message)
