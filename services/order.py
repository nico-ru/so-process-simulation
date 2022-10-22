from typing import Dict, Union
from fastapi import FastAPI, Header
from pydantic.main import BaseModel
from starlette.background import BackgroundTasks
from services.utils.models import Availability, Order

from services.utils.util import get_logger, get_url, send_service_call
from services.utils import config
from services.utils.service import (
    get_process_status,
    insert_process_data,
    pause_process,
    resume_process,
    run_process,
)
from lib.process import Process, Activity, Decision, Sequence

"""
Setting up the server for the order service
"""
name = "order"
server = FastAPI(title=name)
settings = config.Settings()  # type: ignore
logger = get_logger(name)


"""
Specify callback functions for process execution
"""


def check_availability(data: Dict):
    to = get_url("inventory", "inventory")
    message = data.get("message", {})
    send_service_call(name, to, message, data["correlation_id"])


def receive_information(data: Dict):
    # wait for information
    pause_process(name, data["correlation_id"])

    # as 'pause_process' exits the awaited information
    # is received and can be processed
    status = get_process_status(name, data["correlation_id"])
    data.update(availability=status.get("availability"))


def reqeust_invoice(data: Dict):
    to = get_url("billing", "billing")
    message = data.get("message", {})
    send_service_call(name, to, message, data["correlation_id"])


def confirm_order(data: Dict):
    to = get_url("message", "message")
    message = data.get("message", {})
    send_service_call(name, to, message, data["correlation_id"])


def reject_order(data: Dict):
    to = get_url("message", "message")
    inavailable = data["availability"]["inavailable"]
    send_service_call(name, to, inavailable, data["correlation_id"])


"""
Define the process model running in the order service
"""
PROCESS = Process(
    [
        Activity("analyze request"),
        Activity(
            "check availability",
            execution=check_availability,
        ),
        Activity(
            "receive information",
            execution=receive_information,
        ),
        Decision(
            [
                Sequence(
                    [
                        Activity("request invoice", execution=reqeust_invoice),
                        Activity("confirm order", execution=confirm_order),
                    ]
                ),
                Activity("reject order", execution=reject_order),
            ],
            condition=lambda data: 0
            if len(data["availability"]["inavailable"]) == 0
            else 1,
        ),
    ]
)


"""
Register Routes
"""


@server.post(f"/{name}")
async def run(
    order: Order,
    background_tasks: BackgroundTasks,
    correlation_id: Union[str, None] = Header(),
):
    background_tasks.add_task(run_process, name, PROCESS, correlation_id, order)
    return order


@server.post(f"/{name}/availability")
async def receive_availability(
    availability: Availability, correlation_id: Union[str, None] = Header()
):
    if correlation_id is not None:
        insert_process_data(
            name, correlation_id, dict(availability=availability.dict())
        )
        resume_process(name, correlation_id)
    return availability
