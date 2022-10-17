import os
import json
import requests
import datetime
from typing import Dict, Optional
from flask.wrappers import Request

from lib.process import ProcessRunner

USER_DIR = os.path.join(os.path.expanduser("~"))
BASE_DIR = os.environ.get("BASE_DIR", os.path.join(USER_DIR, "process_simulation"))
LOG_DIR = os.environ.get("LOG_DIR", os.path.join(BASE_DIR, "logs"))


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


def log_request(request: Request, service_name: str):
    id = request.headers.get("CORRELATION_ID", type=int)
    now_iso = datetime.datetime.now().isoformat()
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
