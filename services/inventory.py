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
name = "inventory"
server = FastAPI(title=name)
settings = config.Settings()  # type: ignore


"""
Specify callback functions for process execution
"""


def check_inventory(data: Dict):
    data["unavailable_products"] = []
    for product in data["request"].get_json():
        available = random.randint(0, 100) > 10
        if not available:
            data["unavailable_products"].append(product)


def request_reorder(data: Dict):
    to = get_url("purchase")
    send_service_call(to, data, data["correlation_id"])


def send_confirmation(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data, data["correlation_id"])


"""
Define the process model running in the order service
"""

PROCESS = Process(
    [
        Activity(
            "check inverntory",
            execution=check_inventory,
        ),
        Decision(
            [
                Activity(),
                Activity(
                    "request reorder",
                    execution=request_reorder,
                ),
            ],
            condition=lambda data: 1 if len(data["unavailable_products"]) > 0 else 0,
        ),
        Activity(
            "send confirmation",
            execution=send_confirmation,
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
