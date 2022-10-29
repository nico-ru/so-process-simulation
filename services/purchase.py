from datetime import datetime, timedelta
from random import randint
from typing import Dict, Union
from fastapi import FastAPI, Header
from starlette.background import BackgroundTasks
from services.utils.models import Order, ReorderRequest, Success

from services.utils.util import get_logger, get_url, send_service_call
from services.utils import config
from services.utils.service import run_process
from lib.process import Process, Activity

"""
Setting up the server for the order service
"""
name = "purchase"
server = FastAPI(title=name)
settings = config.Settings()  # type: ignore
logger = get_logger(name)


"""
Specify callback functions for process execution
"""


def inform_about_restock(data: Dict):
    order = data["message"]
    reordered_items = list()
    for item in order["items"]:
        id = item["id"]
        available_date = datetime.now() + timedelta(days=randint(7, 31))
        reordered_items.append(dict(id=id, date=str(available_date.date())))
    message = dict(items=reordered_items)

    to = get_url("message", "message")
    send_service_call(name, to, message, data["correlation_id"])


"""
Define the process model running in the order service
and register Routes
"""


@server.post(f"/{name}")
async def run(
    request: ReorderRequest,
    background_tasks: BackgroundTasks,
    correlation_id: Union[str, None] = Header(),
):
    process = Process(
        [
            Activity("reorder inventory"),
            Activity(
                "inform about restock",
                execution=inform_about_restock,
            ),
        ]
    )
    background_tasks.add_task(run_process, name, process, correlation_id, request)
    return Success(success=True)
