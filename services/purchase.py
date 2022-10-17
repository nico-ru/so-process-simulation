import dotenv
from typing import Dict

from utils.service import setup_service, run_service
from utils.util import get_url, send_service_call
from lib.process import Activity, Process

dotenv.load_dotenv()


def inform_about_restock(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data)


PROCESS = Process(
    [
        Activity("reorder inventory"),
        Activity(
            "inform about restock",
            execution=inform_about_restock,
        ),
    ]
)


if __name__ == "__main__":
    purchase = setup_service("purchase", PROCESS)
    run_service(purchase)
