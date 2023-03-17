from random import random
from typing import Dict, Union
from fastapi import FastAPI, Header
from starlette.background import BackgroundTasks
from services.utils.models import InvoiceRequest, Success

from services.utils.util import get_logger, get_url, send_service_call
from services.utils import config
from services.utils.service import run_process
from lib.process import Process, Activity

"""
Setting up the server for the billing service
"""
name = "billing"
server = FastAPI(title=name)
settings = config.Settings()  # type: ignore
logger = get_logger(name)


"""
Specify callback functions for process execution
"""


def send_invoice(data: Dict):
    order = data["message"]
    invoice_items = list()
    total = 0
    for item in order["items"]:
        price = round(random() * 100, 2)
        id = item["id"]
        invoice_items.append(dict(id=id, price=price))
        total += price

    message = dict(items=invoice_items, total=round(total, 2))  # type: ignore

    to = get_url("message", "message")
    send_service_call("Send Invoice", name, to, message, data["correlation_id"])


"""
Define the process model running in the billing service
and register Routes
"""


@server.post(f"/{name}")
async def run(
    request: InvoiceRequest,
    background_tasks: BackgroundTasks,
    correlation_id: Union[str, None] = Header(),
):
    process = Process(
        [
            Activity("prepare invoice", t=7),
            Activity("send invoice", execution=send_invoice, t=3),
        ]
    )
    background_tasks.add_task(run_process, name, process, correlation_id, request)
    return Success(success=True)
