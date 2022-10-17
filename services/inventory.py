import random
import dotenv
from typing import Dict

from utils.util import get_url, send_service_call
from utils.service import setup_service, run_service
from lib.process import Activity, Process, Decision

dotenv.load_dotenv()


def check_inventory(data: Dict):
    data["unavailable_products"] = []
    for product in data["request"].get_json():
        available = random.randint(0, 100) > 10
        if not available:
            data["unavailable_products"].append(product)


def request_reorder(data: Dict):
    to = get_url("purchase")
    send_service_call(to, data)


def send_confirmation(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data)


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


if __name__ == "__main__":
    inventory = setup_service("inventory", PROCESS)
    run_service(inventory)
