import math
import random
from typing import Dict, Union
from fastapi import FastAPI, Header
from starlette.background import BackgroundTasks
from services.utils.models import Order

from services.utils.util import get_logger, get_url, send_service_call
from services.utils import config
from services.utils.service import run_process
from lib.process import Process, Activity, Decision

"""
Setting up the server for the order service
"""
name = "inventory"
server = FastAPI(title=name)
settings = config.Settings()  # type: ignore
logger = get_logger(name)


"""
Specify callback functions for process execution
"""


def check_inventory(data: Dict):
    order = data["message"]

    # compute availability of products
    availability = dict(available=list(), inavailable=list())
    for item in order["items"]:
        qty = item["quantity"]
        available_qty = math.ceil(random.gauss((qty * 1.3), qty))
        if qty > available_qty:
            availability["inavailable"].append(
                {"name": item["name"], "quantity": (available_qty - qty)}
            )
        else:
            availability["available"].append(item)

    # update process status data
    data.update(**availability)


def request_reorder(data: Dict):
    message = {"items": data["inavailable"]}
    to = get_url("purchase", "purchase")
    send_service_call(name, to, message, data["correlation_id"])


def send_confirmation(data: Dict):
    message = {"available": data["available"], "inavailable": data["inavailable"]}
    to = get_url("order", "order/availability")
    send_service_call(name, to, message, data["correlation_id"])


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
            condition=lambda data: 0 if len(data["inavailable"]) == 0 else 1,
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
