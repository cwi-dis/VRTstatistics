import argparse
import sys
import pandas as pd
import matplotlib.pyplot as pyplot
from ..datastore import DataStore

def main():
    parser = argparse.ArgumentParser(description="Plot CSV file")
    parser.add_argument(
        "-o", "--output", metavar="FILE", help="Output plot image file (default: show)"
    )
    parser.add_argument(
        "-x",
        "--x",
        metavar="FIELD",
        default="sessiontime",
        help="FIELD is x-axis",
    )
    parser.add_argument(
        "-p",
        "--predicate",
        metavar="EXPR",
        default=None,
        help="If specified plot only data that matches EXPR predicate"
    )
    parser.add_argument("csvfile", help="CSV datafile to plot")
    parser.add_argument(
        "fields", default=None, nargs="*", metavar="FIELD", help="Fields to plot (default: all)"
    )
    args = parser.parse_args()
    predicate = None
    if args.predicate:
        predicate = compile(args.predicate, "<string>", "eval")
    fields = None
    if args.fields:
        fields = args.fields
    if args.x and fields and not args.x in fields:
        fields = fields + [args.x]
    datastore = DataStore(args.csvfile)
    datastore.load()
    dataframe = datastore.get_dataframe(predicate=predicate, columns=fields)
    plot(dataframe, output=args.output, x=args.x, fields=args.fields)

def plot(data, output=None, x=None, fields=None):
    """
    Plot data (optionally after converting to pandas.DataFrame).
    output is optional output file (default: show in a window)
    x is name of x-axis field
    fields is list of fields to plot (default: all, except x)
    """
    if fields:
        plot = data.interpolate().plot(x=x, y=fields)
    else:
        plot = data.interpolate().plot(x=x)
    if output:
        pyplot.savefig(output)
    else:
        pyplot.show()


if __name__ == "__main__":
    main()
