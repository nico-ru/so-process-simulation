import json
import os
import random
import string
import uuid
import logging
import requests
import datetime
import re
from pathlib import Path
from typing import Dict, Optional, Union

from lib.process import ProcessRunner
from services.utils.config import Settings

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
    activity: str,
    sender: str,
    endpoint: str,
    data: Dict,
    correlation_id: str,
    headers: Dict = dict(),
):
    _headers = {"correlation-id": correlation_id}
    log_event(endpoint, data, sender, activity, correlation_id)
    return requests.post(endpoint, json=data, headers=dict(**_headers, **headers))


def get_url(service: str, operation: Optional[str] = None):
    host = os.getenv("HOST")
    port = os.getenv(f"{service.upper()}_PORT")
    if operation is not None:
        return f"http://{host}:{port}/{operation}"
    return f"http://{host}:{port}/"


def log_event(
    endpoint: str,
    data: Dict,
    service_name: str,
    activity: str,
    id: Union[str, int],
    type: str = "msg",
):
    setting = Settings()
    now = datetime.datetime.now()
    data, timestamp, code = induce_anomaly(data, now)
    message = json.dumps(data)

    if code != 0:
        anomaly_file = os.path.join(LOG_DIR, "anomalies.csv")
        with open(anomaly_file, "a") as file:
            file.write(
                f"{id},{timestamp},{service_name},{endpoint},{activity},{code}\n"
            )

    if code == setting.skip_event_code:
        return

    match = re.search(r"http:\/\/\w+:\d+\/(?P<endpoint>.+)", endpoint)
    if match is not None:
        endpoint = match.group("endpoint")

    m_file_name = f"{uuid.uuid4()}.log.{type}"
    m_file = os.path.join(LOG_DIR, "process", service_name, "messages", m_file_name)
    with open(m_file, "w") as file:
        file.write(message)

    a_file = os.path.join(LOG_DIR, "process", service_name, "annotations.log.csv")
    with open(a_file, "a") as file:
        line = f"{id},{m_file_name},{timestamp},{service_name},{endpoint},{activity},{code}\n"
        file.write(line)
        if code == setting.repeat_event_code:
            file.write(line)


def log_runner(runner: ProcessRunner, service_name: str):
    runner.get_data_frame().to_csv(
        os.path.join(LOG_DIR, "process", service_name, "process.log.csv"),
        mode="a",
        index=False,
        header=False,
    )


def induce_anomaly(data: Dict, now: datetime.datetime):
    code = 0
    settings = Settings()

    if random.random() < settings.skip_event_rate:
        code += settings.skip_event_code

    if random.random() < settings.repeat_event_rate:
        code += settings.repeat_event_code

    if random.random() < settings.swap_event_rate:
        now = now + datetime.timedelta(seconds=random.randint(15, 30))
        code += settings.swap_event_code

    if random.random() < settings.add_key_rate:
        key = "".join(random.choices(string.ascii_letters, k=5))
        value = "".join(random.choices(string.ascii_letters, k=5))
        data.update({key: value})
        code += settings.add_key_code

    data, modified, skipped = modify_keys(
        data, settings.skip_event_rate, settings.modify_key_rate
    )

    if skipped:
        code += settings.skip_key_code

    if modified:
        code += settings.modify_key_code

    return data, now.isoformat(), code


def modify_keys(d, skip_rate: float, modify_rate: float):
    modified = False
    skipped = False
    for k, v in d.copy().items():
        if isinstance(v, dict):
            d.pop(k)
            if random.random() < skip_rate:
                skipped = True
                continue
            if random.random() < modify_rate:
                modified = True
                k = "".join(random.choices(string.ascii_letters, k=5))
            d[k] = v
            modify_keys(v, skip_rate, modify_rate)
        else:
            d.pop(k)
            if random.random() < skip_rate:
                skipped = True
                continue
            if random.random() < modify_rate:
                modified = True
                k = "".join(random.choices(string.ascii_letters, k=5))
            d[k] = v
    return d, modified, skipped


class ProcessStatus:
    def __init__(self, name: str, correlation_id: str):
        self.name = name
        self.correlation_id = correlation_id

        self.status_file = Path(os.path.join(STORAGE_DIR, f"{name}_{correlation_id}"))

    def read_process_status(self) -> Dict:
        if self.status_file.exists():
            return json.loads(self.status_file.read_text())
        return dict()

    def set_process_status(self, params: Dict) -> None:
        status = self.read_process_status()
        status.update(**params)
        self.status_file.write_text(json.dumps(status))

    def teardown(self):
        self.status_file.unlink(missing_ok=True)

    def waiting(self) -> bool:
        status = self.read_process_status()
        return status.get("waiting", False)
