from typing import Dict, Union
from fastapi import FastAPI, Header
from starlette.background import BackgroundTasks
from services.utils.models import Order

from services.utils.util import get_url, send_service_call
from services.utils import config
from services.utils.service import run_process
from lib.process import Process, Activity

"""
Setting up the server for the order service
"""
name = "inventory"
server = FastAPI(title=name)
settings = config.Settings()  # type: ignore


"""
Specify callback functions for process execution
"""


def inform_about_restock(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data, data["correlation_id"])


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
