import os
import dotenv
import pandas
import argparse
from pathlib import Path

dotenv.load_dotenv()

SERVICES = {"billing", "inventory", "message", "order", "purchase"}
LOG_DIR = os.getenv("LOG_DIR")
assert LOG_DIR, "specify log directory by setting LOG_DIR environment variable"


def main(services):
    compound_name = None

    if services is None:
        services = SERVICES
        compound_name = "all"

    services = sorted(set(services))
    if compound_name is None:
        compound_name = "_".join(services)

    frames = []
    for service in services:
        log_path = os.path.join(LOG_DIR, "process", service, "annotations.log.csv")

        if Path(log_path).exists():
            df = pandas.read_csv(
                log_path,
                index_col=None,
                names=[
                    "CORRELATION_ID",
                    "MESSAGE",
                    "TIMESTAMP",
                    "ENDPOINT",
                ],  # type:ignore
            )
            frames.append(df)

    log = pandas.concat(frames, ignore_index=True)
    log["TIMESTAMP"] = pandas.to_datetime(log["TIMESTAMP"])
    log.sort_values("TIMESTAMP", inplace=True)
    log.reset_index(inplace=True, drop=True)

    dir = os.path.join(LOG_DIR, "compound", compound_name)
    location = os.path.join(dir, "annotations.csv")
    log.to_csv(location, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Merge logs of individual services to a compound log."""
    )
    parser.add_argument(
        "-s",
        "--services",
        nargs="*",
        default=None,
        help="services to include in the compound (default: all services are included)",
    )
    args = parser.parse_args()

    main(**vars(args))
