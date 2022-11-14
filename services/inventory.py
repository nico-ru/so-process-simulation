import math
import random
from typing import Dict, Union
from fastapi import FastAPI, Header
from starlette.background import BackgroundTasks
from services.utils.models import AvailabilityRequest, Success

from services.utils.util import get_logger, get_url, send_service_call
from services.utils import config
from services.utils.service import run_process
from lib.process import Process, Activity, Decision

"""
Setting up the server for the inventory service
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
        qty = item["qty"]
        available_qty = abs(math.ceil(random.gauss((qty * 1.4), qty * 0.5)))
        if qty > available_qty:
            availability["inavailable"].append(
                {"id": item["id"], "missing": abs(available_qty - qty)}
            )
        else:
            availability["available"].append(item["id"])

    # update process status data
    data.update(**availability)


def request_reorder(data: Dict):
    inavailable = data["inavailable"]
    reorder_items = list()
    for item in inavailable:
        reorder_items.append(dict(id=item["id"]))
    message = dict(items=reorder_items)

    to = get_url("purchase", "purchase")
    send_service_call(name, to, message, data["correlation_id"])


def send_confirmation(data: Dict):
    message = {"available": data["available"], "inavailable": data["inavailable"]}

    to = get_url("order", "order/availability")
    send_service_call(name, to, message, data["correlation_id"])


"""
Define the process model running in the inventory service
and register Routes
"""


@server.post(f"/{name}")
async def run(
    request: AvailabilityRequest,
    background_tasks: BackgroundTasks,
    correlation_id: Union[str, None] = Header(),
):
    process = Process(
        [
            Activity("check inverntory", execution=check_inventory, t=10),
            Decision(
                [
                    Activity(),
                    Activity("request reorder", execution=request_reorder, t=5),
                ],
                condition=lambda data: 0 if len(data["inavailable"]) == 0 else 1,
            ),
            Activity("send confirmation", execution=send_confirmation, t=5),
        ]
    )
    background_tasks.add_task(run_process, name, process, correlation_id, request)
    return Success(success=True)
