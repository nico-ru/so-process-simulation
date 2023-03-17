import os
import json
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
                    "ACTIVITY",
                    "CODE",
                ],  # type:ignore
            )
            frames.append(df)

    log = pandas.concat(frames, ignore_index=True)
    log["TIMESTAMP"] = pandas.to_datetime(log["TIMESTAMP"])  # type:ignore
    log.sort_values(["CORRELATION_ID", "TIMESTAMP"], inplace=True)
    log.reset_index(inplace=True, drop=True)

    now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    dir = os.path.join(RESULT_DIR, f"{compound_name}_{now}")
    doc_dir = os.path.join(dir, "documents")
    os.makedirs(doc_dir, exist_ok=True)

    vocab = dict()
    size = 0
    for _, row in log.iterrows():
        service = row["SERVICE"]
        filename = row["MESSAGE"]
        source = os.path.join(LOG_DIR, "process", service, "messages", filename)
        try:
            content = json.load(open(source, "r"))
        except:
            print(source)
            raise Exception
        content_parsed = dict_to_dotlist(content)
        content_combined = " ".join(content_parsed)
        destination = os.path.join(doc_dir, filename)
        with open(destination, "w") as file:
            file.write(content_combined)

        for term in content_combined.split(" "):
            if term in vocab:
                vocab[term] += 1
            else:
                vocab[term] = 1

        if len(content_combined.split(" ")) > size:
            size = len(content_combined.split(" "))

    location = os.path.join(dir, "annotations.csv")
    with open(f"{dir}/vocab.txt", "a") as f:
        for term, freq in vocab.items():
            f.write(f"{term} {freq}\n")

    with open(f"{dir}/size.txt", "a") as f:
        f.write(f"{size}")
    log.to_csv(location, index=False)

    log_df_f = pm4py.format_dataframe(
        log,
        case_id="CORRELATION_ID",
        activity_key="ACTIVITY",
        timestamp_key="TIMESTAMP",
    )
    event_log = pm4py.convert_to_event_log(log_df_f)
    pm4py.write_xes(event_log, os.path.join(dir, "event_log.xes"))

    anomalies_path = os.path.join(LOG_DIR, "anomalies.csv")
    if os.path.exists(anomalies_path):
        anomalies: pandas.DataFrame = pandas.read_csv(
            anomalies_path,
            header=None,  # type: ignore
            names=[  # type: ignore
                "CORRELATION_ID",
                "TIMESTAMP",
                "SERVICE",
                "ENDPOINT",
                "ACTIVITY",
                "CODE",
            ],
        )
        anomalies.to_csv(os.path.join(dir, "anomalies.csv"), index=False)


def dict_to_dotlist(data, prefix=""):
    result = []
    if isinstance(data, list):
        for i, value in enumerate(data):
            next_prefix = f"{prefix}.{str(i)}"
            result.extend(dict_to_dotlist(value, prefix=next_prefix))

    elif isinstance(data, dict):
        for key, value in data.items():
            next_prefix = f"{prefix}.{key}" if prefix != "" else key
            result.extend(dict_to_dotlist(value, prefix=next_prefix))
    else:
        item = f"{prefix} {str(data)}"
        result.append(item)
    return result


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
