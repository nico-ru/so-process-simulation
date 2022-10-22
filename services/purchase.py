from typing import Dict, Union
from fastapi import FastAPI, Header
from starlette.background import BackgroundTasks
from services.utils.models import Order

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
    message = data["message"]
    to = get_url("message", "message")
    send_service_call(name, to, message, data["correlation_id"])


"""
Define the process model running in the order service
"""

PROCESS = Process(
    [
        Activity("reorder inventory"),
        Activity(
            "inform about restock",
            execution=inform_about_restock,
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
