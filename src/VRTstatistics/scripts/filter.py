import sys
import os
import json
import time
import types
import csv
import argparse
from typing import Callable, List
from ..datastore import DataStore


def main():
    parser = argparse.ArgumentParser(description="Filter datastore or CSV file")
    parser.add_argument("-d", "--datastore", required=True, help="datastore or CSV datafile to filter")
    parser.add_argument(
        "-o", "--output", metavar="FILE", help="Output datastore or CSV file"
    )
    parser.add_argument(
        "-p",
        "--predicate",
        metavar="EXPR",
        default=None,
        help="If specified plot only data that matches EXPR predicate"
    )
    parser.add_argument(
        "fields", default=None, nargs="*", metavar="FIELD", help="Field mappings to plot (default: all)"
    )
    args = parser.parse_args()
    if len(sys.argv) < 4:
        print(
            f"Usage: {sys.argv[0]} datastore output-json-or-csv predicate [field [...]]"
        )
        sys.exit(1)
    datastore = DataStore(args.datastore)
    datastore.load()
    predicate = None
    fields = None
    if args.fields:
        fields = args.fields
    output = datastore.filter(args.predicate, fields)
    output.filename = args.output
    output.save()
    sys.exit(0)


if __name__ == "__main__":
    main()
