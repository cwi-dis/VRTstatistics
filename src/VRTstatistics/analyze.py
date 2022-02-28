from __future__ import annotations
import fnmatch
from typing import List, Optional
import matplotlib.pyplot as pyplot
import pandas as pd
from .datastore import DataStore, DataStoreError

__all__ = ["plot_simple", "plot_dataframe", "TileCombiner", "SessionTimeFilter"]

def plot_simple(datastore : DataStore, *, predicate=None, title=None, noshow=False, x="sessiontime", fields=None, datafilter=None, plotargs={}) -> pyplot.Axes:
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
    fields_to_plot = None # For simple plots we use all fields (except x, which is automatically ignored)
    if not fields_to_retrieve:
        fields_to_retrieve = None
    dataframe = datastore.get_dataframe(predicate=predicate, fields=fields_to_retrieve)
    if datafilter:
        dataframe = datafilter(dataframe)
    descr = datastore.annotator.description()
    return plot_dataframe(dataframe, title=title, noshow=noshow, x=x, fields=fields_to_plot, descr=descr, plotargs=plotargs)

def plot_dataframe(dataframe : pd.DataFrame, *, title=None, noshow=False, x=None, fields=None, descr=None, plotargs={}) -> pyplot.Axes:
    if fields:
        plot = dataframe.interpolate().plot(x=x, y=fields, **plotargs)
    else:
        plot = dataframe.interpolate().plot(x=x, **plotargs)
    if descr:
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        plot.text(0.98, 0.98, descr, transform=plot.transAxes, verticalalignment='top', horizontalalignment='right', fontsize='x-small', bbox=props)
    if title:
        pyplot.title(title)
    plot.legend(loc='upper left', fontsize='small')
    if not noshow:
        pyplot.show()
    return plot

class DataFrameFilter:
    previous_filter : Optional[DataFrameFilter]

    def __init__(self):
        self.previous_filter = None

    def __add__(self, other : DataFrameFilter) -> DataFrameFilter:
        other.previous_filter = self
        return other

    def __call__(self, dataframe : pd.DataFrame) -> pd.DataFrame:
        if self.previous_filter:
            dataframe = self.previous_filter(dataframe)
        dataframe = self._apply(dataframe)
        return dataframe

    def _apply(self, dataframe : pd.DataFrame) -> pd.DataFrame:
        return dataframe

class SessionTimeFilter(DataFrameFilter):

    def _apply(self, dataframe : pd.DataFrame) -> pd.DataFrame:
        dataframe = dataframe[dataframe["sessiontime"] >= 0]
        return dataframe

class TileCombiner(DataFrameFilter):

    def __init__(self, pattern : str, column : str, function : str, combined : bool = False, keep : bool = False) -> None:
        super().__init__()
        self.pattern = pattern
        self.column = column
        self.function = function
        self.combined = combined
        self.keep = keep

    def _apply(self, dataframe : pd.DataFrame) -> pd.DataFrame:
        if self.previous_filter:
            dataframe = self.previous_filter(dataframe)
        column_names = self._get_column_names(dataframe, self.pattern)
        if not column_names:
            print(f'Warning: pattern {self.pattern} did not select any columns. Returning dataframe as-is.')
            return dataframe
        columns = []
        rv = None
        for n in column_names:
            # Create scaffolding (sessiontimes) if we haven't done so.
            filter = dataframe[n].notna()
            if rv is None:
                rv = dataframe[filter].copy()
                rv.drop(column_names, axis=1, inplace=True)
                # rv = rv["sessiontime"]
            # filter out values for this column
            c = dataframe.loc[filter, n]
            
            # Insert
            new_values = list(c)
            while len(new_values) < len(rv):
                new_values.append(0)
            while len(new_values) > len(rv):
                new_values = new_values[:-1]
            rv[n] = new_values
        # Now sum the relevant columns
        if self.function == "sum":
            rv[self.column] = rv[column_names].sum(axis=1)
        elif self.function == "mean":
            rv[self.column] = rv[column_names].mean(axis=1)
        elif self.function == "min":
            rv[self.column] = rv[column_names].min(axis=1)
        elif self.function == "max":
            rv[self.column] = rv[column_names].max(axis=1)
        else:
            raise DataStoreError(f"Unknown function {self.function}")
        rv.drop(column_names, axis=1, inplace=True)
        if self.combined:
            orig_columns = list(dataframe.keys())
            rv_columns = list(rv.keys())
            todrop_columns = []
            for c in orig_columns:
                if c in rv_columns:
                    todrop_columns.append(c)
            rv.drop(todrop_columns, axis=1, inplace=True)
            rv = dataframe.join(rv)
            if not self.keep:
                rv.drop(column_names, axis=1, inplace=True)
        return rv

    def _get_column_names(self, dataframe : pd.DataFrame, pattern) -> List[str]:
        all_columns = list(dataframe.keys())
        rv = []
        for col in all_columns:
            if fnmatch.fnmatchcase(col, pattern):
                rv.append(col)
        return rv
