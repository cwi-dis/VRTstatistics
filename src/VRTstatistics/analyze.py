import matplotlib.pyplot as pyplot
from .datastore import DataStore

def plot_simple(datastore : DataStore, *, predicate=None, title=None, output=None, x=None, fields=None):
    """
    Plot data (optionally after converting to pandas.DataFrame).
    output is optional output file (default: show in a window)
    x is name of x-axis field
    fields is list of fields to plot (default: all, except x)
    """
    fields_to_retrieve = list(fields)
    fields_to_plot = fields
    # If we have specified fields to retrieve ensure our x-axis is in the list
    if fields_to_retrieve and x and not x in fields_to_retrieve:
        fields_to_retrieve.append(x)
    fields_to_plot = None
    if not fields_to_retrieve:
        fields_to_retrieve = None
    data = datastore.get_dataframe(predicate=predicate, columns=fields_to_retrieve)
    if fields_to_plot:
        plot = data.interpolate().plot(x=x, y=fields_to_plot)
    else:
        plot = data.interpolate().plot(x=x)
    if title:
        pyplot.title(title)
    if output:
        pyplot.savefig(output)
    else:
        pyplot.show()
