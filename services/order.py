import dotenv
from typing import Dict

from utils.util import get_url, send_service_call
from services.utils.service import setup_service, run_service
from lib.process import Process, Activity, Decision, Sequence

dotenv.load_dotenv()


def check_availability(data: Dict):
    to = get_url("inventory", "inventory")
    send_service_call(to, data)


def receive_information(data: Dict):
    pass


def reqeust_invoice(data: Dict):
    to = get_url("billing", "billing")
    send_service_call(to, data)


def confirm_order(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data)


def reject_order(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data)


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
                            execution=reqeust_invoice,
                        ),
                        Activity(
                            "confirm order",
                            execution=confirm_order,
                        ),
                    ]
                ),
                Activity(
                    "reject order",
                    execution=reject_order,
                ),
            ],
            [60, 40],
        ),
    ]
)


if __name__ == "__main__":
    order = setup_service("order", PROCESS)
    run_service(order)
