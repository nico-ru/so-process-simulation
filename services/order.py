from datetime import datetime, timedelta
from random import randint, random
from typing import Dict, Union
from fastapi import FastAPI, Header
from starlette.background import BackgroundTasks
from services.utils.models import Availability, Order, Success

from services.utils.util import get_logger, get_url, send_service_call
from services.utils import config
from services.utils.service import (
    end_process,
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
    order = data.get("message", {})
    message = dict(items=order["items"])

    to = get_url("inventory", "inventory")
    send_service_call(name, to, message, data["correlation_id"])


def receive_information(data: Dict):
    # wait for information
    pause_process(name, data["correlation_id"])

    # as 'pause_process' exits the awaited information
    # is received and can be processed
    status = get_process_status(name, data["correlation_id"])
    data.update(availability=status.get("availability"))


def reqeust_invoice(data: Dict):
    order = data.get("message", {})
    message = dict(items=order["items"])

    to = get_url("billing", "billing")
    send_service_call(name, to, message, data["correlation_id"])


def confirm_order(data: Dict):
    arrive_date = datetime.now() + timedelta(days=randint(1, 14))
    message = dict(date=str(arrive_date.date()))

    to = get_url("message", "message")
    send_service_call(name, to, message, data["correlation_id"])


def reject_order(data: Dict):
    inavailable = data["availability"]["inavailable"]
    message = dict(items=inavailable)

    to = get_url("message", "message")
    send_service_call(name, to, message, data["correlation_id"])


def teardown(data: Dict):
    end_process(name, data["correlation_id"])


"""
Define the process model running in the order service
and register Routes
"""


@server.post(f"/{name}")
async def run(
    order: Order,
    background_tasks: BackgroundTasks,
    correlation_id: Union[str, None] = Header(),
):
    process = Process(
        [
            Activity("analyze request"),
            Activity("check availability", execution=check_availability, t=1),
            Activity(
                "receive information",
                execution=receive_information,
            ),
            Decision(
                [
                    Sequence(
                        [
                            Activity("request invoice", execution=reqeust_invoice, t=3),
                            Activity("confirm order", execution=confirm_order, t=4),
                        ]
                    ),
                    Activity("reject order", execution=reject_order, t=5),
                ],
                condition=lambda data: 0
                if len(data["availability"]["inavailable"]) == 0
                else 1,
            ),
            Activity(execution=teardown),
        ]
    )
    background_tasks.add_task(run_process, name, process, correlation_id, order)
    return Success(success=True)


@server.post(f"/{name}/availability")
async def receive_availability(
    availability: Availability, correlation_id: Union[str, None] = Header()
):
    if correlation_id is not None:
        insert_process_data(
            name, correlation_id, dict(availability=availability.dict())
        )
        resume_process(name, correlation_id)
    return Success(success=True)
