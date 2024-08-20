import argparse
import sys
import os

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
    parser.add_argument("--pausefordebug", action="store_true", help="Wait for a newline after start (so you can attach a debugger)")
    args = parser.parse_args()
    if args.pausefordebug:
        sys.stderr.write(f"Attach debugger to pid={os.getpid()}. Press return to continue - ")
        sys.stderr.flush()
        sys.stdin.readline()

    if len(sys.argv) < 4:
        print(
            f"Usage: {sys.argv[0]} datastore output-json-or-csv predicate [field [...]]"
        )

        sys.exit(1)

    datastore = DataStore(args.datastore)
    datastore.load()

    fields = None

    if args.fields:
        fields = args.fields

    output = datastore.filter(args.predicate, fields)
    output.filename = args.output
    output.save()

    sys.exit(0)


if __name__ == "__main__":
    main()
