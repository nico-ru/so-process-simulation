import os
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request
from flask.logging import default_handler

from lib.process import Process, ProcessRunner
from .util import LOG_DIR, log_request, log_runner


def setup_service(name: str, process: Process) -> Flask:
    server = Flask(name)
    configure_service(server)

    def run_process():
        log_request(request, name)
        runner = ProcessRunner(process)
        runner.data["request"] = request
        runner.execute(case_id=request.headers.get("CORRELATION_ID", type=int))
        log_runner(runner, name)
        return jsonify(success=True)

    server.add_url_rule(f"/{name}", name, run_process, methods=["POST"])
    return server


def configure_service(service: Flask):
    # create logging directories
    server_log_dir = os.path.join(LOG_DIR, "server")
    Path(server_log_dir).mkdir(parents=True, exist_ok=True)

    message_dir = os.path.join(LOG_DIR, "process", service.name, "messages")
    Path(message_dir).mkdir(parents=True, exist_ok=True)

    # setup file logger
    service.logger.removeHandler(default_handler)
    handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "server", f"{service.name}.log")
    )
    handler.setLevel(logging.INFO)
    service.logger.addHandler(handler)
    service.config.update(ENV=os.getenv("FLASK_ENV"))


def run_service(service: Flask):
    host = os.getenv("FLASK_RUN_HOST", "localhost")
    port = int(os.getenv(f"{service.name.upper()}_FLASK_RUN_PORT", 5000))
    debug = bool(os.getenv("FLASK_DEBUG", False))
    service.run(host=host, port=port, load_dotenv=False, debug=debug)
