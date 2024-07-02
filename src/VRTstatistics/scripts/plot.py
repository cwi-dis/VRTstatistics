import argparse
import sys
import matplotlib.pyplot as pyplot
from ..datastore import DataStore
from ..plots import plot_simple

def main():
    parser = argparse.ArgumentParser(description="Plot datastore or CSV file")
    parser.add_argument("-d", "--datastore", required=True, help="datastore or CSV datafile to plot")
    parser.add_argument(
        "-o", "--output", metavar="FILE", help="Output plot image file (default: show)"
    )
    parser.add_argument(
        "-p",
        "--predicate",
        metavar="EXPR",
        default=None,
        help="If specified plot only data that matches EXPR predicate"
    )
    parser.add_argument(
        "-x",
        "--x",
        metavar="FIELD",
        default="sessiontime",
        help="FIELD is x-axis",
    )
    parser.add_argument(
        "-t",
        "--title",
        metavar="TITLE",
        default=None,
        help="Set plot title",
    )
    parser.add_argument(
        "fields", default=None, nargs="*", metavar="FIELD", help="Field mappings to plot (default: all)"
    )
    args = parser.parse_args()
    predicate = None
    datastore = DataStore(args.datastore)
    datastore.load()
    plt = plot_simple(datastore, title=args.title, noshow=not not args.output, predicate=args.predicate, x=args.x, fields=args.fields)
    if args.output:
        pyplot.savefig(args.output)


if __name__ == "__main__":
    main()
