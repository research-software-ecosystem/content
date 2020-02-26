import json
import os
import sys
import glob
import argparse

import requests


def clean():
    for data_file in glob.glob(r"../../data/*/*.json"):
        filename_ext = os.path.basename(data_file).split(".")
        if len(filename_ext) == 2 and filename_ext[1] == "json":
            os.remove(data_file)


def retrieve(filters=None):
    """
    Go through bio.tools entries using its API and save the JSON files
    in the right folders
    """

    i = 1
    nb_tools = 1
    has_next_page = True
    filters = filters or {}
    while has_next_page:
        parameters = {**filters, **{"page": i}}
        response = requests.get(
            "https://bio.tools/api/tool/",
            params=parameters,
            headers={"Accept": "application/json"},
        )
        try:
            entry = response.json()
        except JSONDecodeError as e:
            print("Json decode error for " + str(req.data.decode("utf-8")))
            break
        has_next_page = entry["next"] != None

        for tool in entry["list"]:
            tool_id = tool["biotoolsID"]
            tpe_id = tool_id.lower()
            directory = os.path.join("..", "..", "data", tpe_id)
            if not os.path.isdir(directory):
                os.mkdir(directory)
            with open(os.path.join(directory, tpe_id + ".json"), "w") as write_file:
                json.dump(
                    tool, write_file, sort_keys=True, indent=4, separators=(",", ": ")
                )
            nb_tools += 1
            print(f"import tool #{nb_tools}: {tool_id} in folder {directory}")
        i += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="biotools to bioschemas bot script")
    parser.add_argument(
        "collection", type=str, default="*", nargs="?", help="collection name filter"
    )
    args = parser.parse_args()
    clean()
    if args.collection == "*":
        retrieve()
    else:
        retrieve(filters={"collection": args.collection})
