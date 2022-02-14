import argparse
import sys
import pandas as pd
import matplotlib.pyplot as pyplot

def main():
    parser = argparse.ArgumentParser(description="Plot CSV file")
    parser.add_argument("-o", "--output", metavar="FILE", help="Output plot image file (default: show)")
    parser.add_argument("-x", "--x", metavar="FIELD", default="sessiontime", help="FIELD is x-axis (default: sessiontime)")
    parser.add_argument("csvfile", help="CSV datafile to plot")
    parser.add_argument("fields", nargs="*", metavar="FIELD", help="Fields to plot (default: all)")
    args = parser.parse_args()
    data = pd.read_csv(args.csvfile)
    plot(data, output=args.output, x=args.x, fields=args.fields)

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

if __name__ == '__main__':
    main()
    