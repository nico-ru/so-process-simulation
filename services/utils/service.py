import time
from typing import Dict, Union
from pydantic.main import BaseModel

from lib.process import Process, ProcessRunner
from .util import ProcessStatus, log_runner


def run_process(
    name: str, process: Process, correlation_id: Union[str, None], data: BaseModel
):
    runner = ProcessRunner(process, realtime=True)
    runner.data["correlation_id"] = correlation_id
    runner.data["message"] = data.dict()
    runner.execute(case_id=correlation_id)
    log_runner(runner, name)


def pause_process(name: str, correlation_id: str):
    status = ProcessStatus(name, correlation_id)
    status.set_process_status(dict(waiting=True))
    while status.waiting():
        time.sleep(0.1)


def resume_process(name: str, correlation_id: str):
    status = ProcessStatus(name, correlation_id)
    status.set_process_status(dict(waiting=False))


def insert_process_data(name: str, correlation_id: str, data: Dict):
    status = ProcessStatus(name, correlation_id)
    status.set_process_status(data)


def get_process_status(name: str, correlation_id: str):
    return ProcessStatus(name, correlation_id).read_process_status()


def end_process(name: str, correlation_id: str):
    ProcessStatus(name, correlation_id).teardown()
