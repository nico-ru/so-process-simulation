import json
import os
import uuid
import logging
import requests
import datetime
from pathlib import Path
from typing import Dict, Optional, Union

from lib.process import ProcessRunner

USER_DIR = os.path.join(os.path.expanduser("~"))
BASE_DIR = os.environ.get("BASE_DIR", os.path.join(USER_DIR, "process_simulation"))
LOG_DIR = os.environ.get("LOG_DIR", os.path.join(BASE_DIR, "logs"))
STORAGE_DIR = os.environ.get("STORAGE_DIR", os.path.join(BASE_DIR, "runtime"))


def get_logger(name):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(
        filename=os.path.join(LOG_DIR, "server", f"{name}_DEBUG.log")
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(module)s - %(funcName)s - line:%(lineno)d - %(levelname)s - %(message)s"
    )

    fh.setFormatter(formatter)
    logger.addHandler(fh)  # Exporting logs to a file
    return logger


def send_service_call(
    sender: str, endpoint: str, data: Dict, correlation_id: str, headers: Dict = dict()
):
    _headers = {"correlation-id": correlation_id}
    log_event(endpoint, json.dumps(data), sender, correlation_id)
    return requests.post(endpoint, json=data, headers=dict(**_headers, **headers))


def get_url(service: str, operation: Optional[str] = None):
    host = os.getenv("HOST")
    port = os.getenv(f"{service.upper()}_PORT")
    if operation is not None:
        return f"http://{host}:{port}/{operation}"
    return f"http://{host}:{port}/"


def log_event(
    endpoint: str,
    data: str,
    service_name: str,
    id: Union[str, int],
    type: str = "msg",
):
    now_iso = datetime.datetime.now().isoformat()

    m_file_name = f"{uuid.uuid4()}.log.{type}"
    m_file = os.path.join(LOG_DIR, "process", service_name, "messages", m_file_name)
    with open(m_file, "w") as file:
        file.write(data)

    a_file = os.path.join(LOG_DIR, "process", service_name, "annotations.log.csv")
    with open(a_file, "a") as file:
        file.write(f"{id},{m_file_name},{now_iso},{service_name},{endpoint}\n")


def log_runner(runner: ProcessRunner, service_name: str):
    runner.get_data_frame().to_csv(
        os.path.join(LOG_DIR, "process", service_name, "process.log.csv"),
        mode="a",
        index=False,
        header=False,
    )


class ProcessStatus:
    def __init__(self, name: str, correlation_id: str):
        self.name = name
        self.correlation_id = correlation_id

        self.status_file = Path(os.path.join(STORAGE_DIR, f"{name}_{correlation_id}"))

    def read_process_status(self):
        if self.status_file.exists():
            return json.loads(self.status_file.read_text())
        return dict()

    def set_process_status(self, params: Dict):
        status = self.read_process_status()
        status.update(**params)
        self.status_file.write_text(json.dumps(status))

    def waiting(self):
        status = self.read_process_status()
        return status.get("waiting", False)
