from __future__ import annotations
import fnmatch
from typing import List, Optional
import matplotlib.pyplot as pyplot
import pandas as pd
from .datastore import DataStore, DataStoreError

__all__ = ["DataFrameFilter", "TileCombiner", "SessionTimeFilter"]


class DataFrameFilter:
    """A DataFrameFiler is a callable object. It accepts a dataframe and returns
    a copy of that dataframe with filtering applied.
    
    DataFrameFilters can be added. This modifies the RHS filter to apply the LHS
    filter before itself and returns the RHS filter.
    
    Not elegant, but it means filters can be stacked left-to-right with +.
    """
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
    """
    DataFrameFilter that removes all items with sessiontime < 0
    """

    def _apply(self, dataframe : pd.DataFrame) -> pd.DataFrame:
        dataframe = dataframe[dataframe["sessiontime"] >= 0]
        return dataframe

class TileCombiner(DataFrameFilter):
    """
    DafaFrameFilter that combines columns matching a pattern into a new column.

    pattern - A (shell-like) pattern selecting one or more columns
    column - name of the output column
    function - Function to apply to the fields: sum/mean/max/min
    combined - don't remember
    keep - Keep the original columns selected by pattern, otherwise drop them.
    optional - don't complain if pattern doesn't match anything, return the dataFrama as-is.
    """

    def __init__(self, pattern : str, column : str, function : str, combined : bool = False, keep : bool = False, optional : bool = False) -> None:
        super().__init__()
        self.pattern = pattern
        self.column = column
        self.function = function
        self.combined = combined
        self.keep = keep
        self.optional = optional
        self.didwarn = False

    def _apply(self, dataframe : pd.DataFrame) -> pd.DataFrame:
        if self.previous_filter:
            dataframe = self.previous_filter(dataframe)
        column_names = self._get_column_names(dataframe, self.pattern)
        if not column_names:
            if not self.optional and not self.didwarn:
                print(f'Warning: pattern {self.pattern} did not select any columns. Returning dataframe as-is.')
                self.didwarn = True
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

def _df_to_pc_index_1(df : pd.DataFrame, column : str) -> pd.DataFrame:
    """Helper - convert a single column from time->index mapping into index->time mapping"""
    tmp = df[["sessiontime", column]].dropna()
    filter = tmp[column] > 0
    tmp = tmp[filter].copy()
    tmp.loc[:,'pc_index'] = tmp[column]
    tmp[column+'.sessiontime'] = tmp['sessiontime']
    tmp.drop(['sessiontime', column], axis=1, inplace=True)
    tmp.set_index('pc_index', inplace=True)
    return tmp

def _df_to_pc_index(df : pd.DataFrame, columns : List[str]) -> pd.DataFrame:
    """Helper - convert a set of columns from sessiontime-indexed into pcindex-indexed"""
    all = []
    for c in columns:
        all.append(_df_to_pc_index_1(df, c))
    rv = all[0]
    rv = rv.join(all[1:])
    return rv
    
def dataframe_to_pcindex_for_tile(dataframe : pd.DataFrame, tilenum : int, include_sender : bool=False) -> pd.DataFrame:
    """Convert a sessiontime-indexed dataframe to a pcindex-indexed dataframe"""
    cols = [
        f'receiver.pc.reader.{tilenum}', 
        f'receiver.pc.decoder.{tilenum}', 
        f'receiver.pc.preparer.{tilenum}'
        ]
    if include_sender:
        cols.insert(0, f'sender.pc.writer.{tilenum}')
    return _df_to_pc_index(dataframe, cols)

def dataframe_to_pcindex_latencies_for_tile(dataframe : pd.DataFrame, tilenum : int) -> pd.DataFrame:
    rv = dataframe_to_pcindex_for_tile(dataframe, tilenum, include_sender=False)
    basecol = rv[f'receiver.pc.reader.{tilenum}.sessiontime']
    
    rv[f'receiver.pc.preparer.{tilenum}.latency'] = rv[f'receiver.pc.preparer.{tilenum}.sessiontime'] - basecol
    rv[f'receiver.pc.decoder.{tilenum}.latency'] = rv[f'receiver.pc.decoder.{tilenum}.sessiontime'] - basecol
    rv[f'sessiontime'] = rv[f'receiver.pc.reader.{tilenum}.sessiontime']
    rv.drop(f'receiver.pc.preparer.{tilenum}.sessiontime', axis=1, inplace=True)
    rv.drop(f'receiver.pc.decoder.{tilenum}.sessiontime', axis=1, inplace=True)
    rv.drop(f'receiver.pc.reader.{tilenum}.sessiontime', axis=1, inplace=True)
    return rv
