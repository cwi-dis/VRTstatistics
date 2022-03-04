from __future__ import annotations
import fnmatch
from typing import List, Optional
import matplotlib.pyplot as pyplot
import pandas as pd
from .datastore import DataStore, DataStoreError

__all__ = ["TileCombiner", "SessionTimeFilter"]


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
