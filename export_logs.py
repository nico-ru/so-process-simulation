import os
import pm4py
import dotenv
import pandas
import shutil
import datetime
import argparse

dotenv.load_dotenv()

SERVICES = {"billing", "inventory", "message", "order", "purchase"}
LOG_DIR = os.getenv("LOG_DIR")
RESULT_DIR = os.getenv("RESULT_DIR")
assert LOG_DIR, "specify log directory by setting LOG_DIR environment variable"
assert RESULT_DIR, "specify result directory by setting RESULT_DIR environment variable"


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

        if os.path.exists(log_path):
            df = pandas.read_csv(
                log_path,
                index_col=None,
                names=[
                    "CORRELATION_ID",
                    "MESSAGE",
                    "TIMESTAMP",
                    "SERVICE",
                    "ENDPOINT",
                ],  # type:ignore
            )
            frames.append(df)

    log = pandas.concat(frames, ignore_index=True)
    log["TIMESTAMP"] = pandas.to_datetime(log["TIMESTAMP"])  # type:ignore
    log.sort_values("TIMESTAMP", inplace=True)
    log.reset_index(inplace=True, drop=True)

    now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    dir = os.path.join(RESULT_DIR, f"{compound_name}_{now}")
    doc_dir = os.path.join(dir, "documents")
    os.makedirs(doc_dir, exist_ok=True)

    for _, row in log.iterrows():
        service = row["SERVICE"]
        filename = row["MESSAGE"]
        source = os.path.join(LOG_DIR, "process", service, "messages", filename)
        destination = os.path.join(doc_dir, filename)
        shutil.copy(source, destination)

    location = os.path.join(dir, "annotations.csv")
    log.to_csv(location, index=False)

    log_df_f = pm4py.format_dataframe(
        log,
        case_id="CORRELATION_ID",
        activity_key="ENDPOINT",
        timestamp_key="TIMESTAMP",
    )
    event_log = pm4py.convert_to_event_log(log_df_f)
    pm4py.write_xes(event_log, os.path.join(dir, "event_log.xes"))


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
