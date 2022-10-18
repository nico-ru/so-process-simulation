import random
import time
from typing import Dict, Union
from fastapi import FastAPI, Header
from starlette.background import BackgroundTasks
from services.utils.models import Order

from services.utils.util import get_url, send_service_call
from services.utils import config
from services.utils.service import run_process
from lib.process import Process, Activity, Decision, Sequence

"""
Setting up the server for the order service
"""
name = "order"
server = FastAPI(title=name)
settings = config.Settings()  # type: ignore


"""
Specify callback functions for process execution
"""


def check_availability(data: Dict):
    to = get_url("inventory", "inventory")
    send_service_call(to, data, data["correlation_id"])


def receive_information(data: Dict):
    duration = random.randint(1, 5)
    time.sleep(duration)


def reqeust_invoice(data: Dict):
    to = get_url("billing", "billing")
    send_service_call(to, data, data["correlation_id"])


def confirm_order(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data, data["correlation_id"])


def reject_order(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data, data["correlation_id"])


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
                        Activity(
                            "request invoice",
                            execution=receive_information,
                        ),
                        Activity(
                            "confirm order",
                            execution=receive_information,
                        ),
                    ]
                ),
                Activity(
                    "reject order",
                    execution=receive_information,
                ),
            ],
            [60, 40],
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
