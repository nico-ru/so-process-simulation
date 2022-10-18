from typing import Union
from pydantic.main import BaseModel

from lib.process import Process, ProcessRunner
from .util import log_runner


def run_process(
    name: str, process: Process, correlation_id: Union[str, None], data: BaseModel
):
    runner = ProcessRunner(process)
    runner.data["correlation_id"] = correlation_id
    runner.data["message"] = data
    runner.execute(case_id=correlation_id)
    log_runner(runner, name)
