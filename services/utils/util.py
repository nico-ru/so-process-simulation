import logging
import os
import json
import requests
import dotenv
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask.wrappers import Request
from flask.logging import default_handler

from lib.process import ProcessRunner

# DEFINE PATH CONSTANTS
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(FILE_DIR, "..", "..")
LOG_DIR = os.path.join(BASE_DIR, "logs")


def run_service(service: Flask):
    dotenv.load_dotenv(os.path.join(BASE_DIR, ".env"))

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

    # setup server config
    service.config.update(ENV=os.environ.get("FLASK_ENV"))
    host = os.environ.get("FLASK_RUN_HOST")
    port = int(os.environ.get(f"{service.name.upper()}_FLASK_RUN_PORT") or 5000)
    service.run(host=host, port=port, load_dotenv=False)


def log_request(request: Request, service_name: str):
    id = request.headers.get("CORRELATION_ID", type=int)
    now_iso = datetime.now().isoformat()
    data = request.get_data()
    path_f = "-".join(list(filter(None, request.path.split("/"))))

    m_file_name = f"{path_f}_{now_iso}.log.req"
    m_file = os.path.join(LOG_DIR, "process", service_name, "messages", m_file_name)
    with open(m_file, "bw") as file:
        file.write(data)

    a_file = os.path.join(LOG_DIR, "process", service_name, "annotations.log.csv")
    with open(a_file, "a") as file:
        file.write(f"{id},{m_file_name},{now_iso},{request.path}\n")


def log_runner(runner: ProcessRunner, service_name: str):
    runner.get_data_frame().to_csv(
        os.path.join(LOG_DIR, "process", service_name, "process.log.csv"),
        mode="a",
        index=False,
        header=False,
    )


def send_service_call(endpoint: str, data: Dict):
    json_data_s = json.dumps(data, default=lambda _: "<not serializable>")
    json_data = json.loads(json_data_s)
    return requests.post(endpoint, json=json_data, headers=data["request"].headers)


def get_url(service: str, operation: Optional[str] = None):
    host = os.environ.get("FLASK_RUN_HOST")
    port = os.environ.get(f"{service.upper()}_FLASK_RUN_PORT")
    if operation is not None:
        return f"http://{host}:{port}/{operation}"
    return f"http://{host}:{port}/"
