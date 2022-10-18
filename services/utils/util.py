import json
import os
import uuid
import requests
import datetime
from pydantic.main import BaseModel
from typing import Dict, Optional, Union

from lib.process import ProcessRunner

USER_DIR = os.path.join(os.path.expanduser("~"))
BASE_DIR = os.environ.get("BASE_DIR", os.path.join(USER_DIR, "process_simulation"))
LOG_DIR = os.environ.get("LOG_DIR", os.path.join(BASE_DIR, "logs"))


def send_service_call(
    endpoint: str, data: Dict, correlation_id: str, headers: Dict = dict()
):
    _headers = dict(correlation_id=correlation_id, **headers)
    return requests.post(endpoint, json=data, headers=_headers)


def get_url(service: str, operation: Optional[str] = None):
    host = os.getenv("HOST")
    port = os.getenv(f"{service.upper()}_PORT")
    if operation is not None:
        return f"http://{host}:{port}/{operation}"
    return f"http://{host}:{port}/"


def log_request(endpoint: str, data: BaseModel, service_name: str, id: Union[str, int]):
    now_iso = datetime.datetime.now().isoformat()
    message = data.json()

    m_file_name = f"{uuid.uuid4()}.log.req"
    m_file = os.path.join(LOG_DIR, "process", service_name, "messages", m_file_name)
    with open(m_file, "w") as file:
        file.write(message)

    a_file = os.path.join(LOG_DIR, "process", service_name, "annotations.log.csv")
    with open(a_file, "a") as file:
        file.write(f"{id},{m_file_name},{now_iso},{endpoint}\n")


def log_runner(runner: ProcessRunner, service_name: str):
    runner.get_data_frame().to_csv(
        os.path.join(LOG_DIR, "process", service_name, "process.log.csv"),
        mode="a",
        index=False,
        header=False,
    )
