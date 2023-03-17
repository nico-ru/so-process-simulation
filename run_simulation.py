import os
import datetime
import argparse
from os.path import isfile
from typing import Dict
import dotenv
import requests
import time
import random
import json
from string import ascii_lowercase

dotenv.load_dotenv()

SIMULATION_DIR_NAME = datetime.datetime.now().strftime("%Y-%d-%m_%H-%M-%S")

USER_DIR = os.path.join(os.path.expanduser("~"))
BASE_DIR = os.environ.get("BASE_DIR", os.path.join(USER_DIR, "process_simulation"))
RUNTIME_DIR = os.environ.get("RUNTIME_DIR", os.path.join(BASE_DIR, "runtime"))

host = os.getenv("HOST", "localhost")
port = int(os.getenv("ORDER_PORT", 5003))

url = f"http://{host}:{port}/order"


def id() -> str:
    """
    function to generate not so unique random product id.
    to simulate webshop with limited number of items
    """
    chars = list(ascii_lowercase[22:]) + [str(i) for i in range(1)]
    return "".join([random.choice(chars) for _ in range(4)])


def get_size() -> str:
    """
    function to generate a random value for the size key
    """
    return random.choice(["XS", "S", "M", "L", "XL"])


def get_location() -> str:
    """
    function to generate random location
    """
    return random.choice(["DE", "AT", "CH"])


def get_payload():
    """
    function to generate random order request payload
    example:
        {
            "items": [
                {"id": y1y0x, "size": "M"},
                {"id": y10z0, "size": "L"},
                {"id": z1011, "size": "S"},
            ]
            "location": "DE"
        }
    """
    number_items = random.randint(1, 15)
    return {
        "items": [{"id": id(), "size": get_size()} for _ in range(number_items)],
        "location": get_location(),
    }


def log_payload(payload: Dict):
    filename = datetime.datetime.now().strftime("%Y-%d-%m_%H-%M-%S_%f")

    simulation_path = os.path.join(
        os.environ["LOG_DIR"], "simulation", SIMULATION_DIR_NAME
    )
    os.makedirs(simulation_path, exist_ok=True)
    location = os.path.join(simulation_path, f"{filename}.json")

    with open(location, "w") as f:
        f.write(json.dumps(payload, indent=2))


def clean_runtime():
    for filename in os.listdir(RUNTIME_DIR):
        if filename.startswith("."):
            continue
        file = os.path.join(RUNTIME_DIR, filename)
        if os.path.isfile(file):
            os.remove(file)


def main(n_requests: int, delay: int):
    clean_runtime()
    for i in range(n_requests):
        headers = {"CORRELATION-ID": str(i), "Content-Type": "application/json"}
        payload = get_payload()
        log_payload(payload)
        requests.request("POST", url, headers=headers, data=json.dumps(payload))

        seconds = abs(random.gauss(delay, (delay * 0.5)))
        time.sleep(seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""run simulation order requests""")
    parser.add_argument(
        "-n",
        "--n_requests",
        default=25,
        type=int,
        help="Number of 'order' requests to send in the simulation (default: 25)",
    )
    parser.add_argument(
        "-d",
        "--delay",
        default=2,
        type=float,
        help="Average delay in seconds between requests (default: .5)",
    )
    args = parser.parse_args()
    main(**vars(args))
