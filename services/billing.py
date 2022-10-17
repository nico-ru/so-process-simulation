import dotenv
from typing import Dict

from utils.util import get_url, send_service_call
from utils.service import setup_service, run_service
from lib.process import Activity, Process


dotenv.load_dotenv()


def send_invoice(data: Dict):
    to = get_url("message", "common")
    send_service_call(to, data)


PROCESS = Process(
    [
        Activity("prepare invoice"),
        Activity(
            "send invoice",
            execution=send_invoice,
        ),
    ]
)


if __name__ == "__main__":
    billing = setup_service("billing", PROCESS)
    run_service(billing)
