from __future__ import annotations
from runpy import run_module
import sys
import json
from typing import Optional, List, Callable, Any
from .parser import StatsFileParser
import pandas

__all__ = ["DataStoreRecord", "DataStore", "DataStoreError", "combine"]

class DataStoreError(RuntimeError):
    pass

DataStoreRecord = dict[str, Any]


class DataStore:
    debug = True

    filename: str
    data: list[DataStoreRecord]
    annotator : Any
   
    def __init__(self, filename: Optional[str] = None) -> None:
        self.filename = filename
        self.data = []
        self.annotator = None

    def load(self) -> None:
        assert self.filename
        if self.filename == "-":
            pass
        elif self.filename.endswith(".json"):
            self.load_json()
        elif self.filename.endswith(".log"):
            self.load_log()
        elif self.filename.endswith(".csv"):
            self.load_csv()
        else:
            raise DataStoreError(f"Don't know how to load {self.filename}")

    def load_json(self) -> None:
        data = json.load(open(self.filename, "r"))
        metadata = None
        if type(data) != type([]):
            metadata = data["metadata"]
            data = data["data"]
        self.data = data
        if metadata:
            from .annotator import deserialize
            self.annotator = deserialize(self, metadata)

    def load_log(self, nocheck=False) -> None:
        parser = StatsFileParser(self.filename)
        self.data = parser.parse()
        if not nocheck:
            parser.check()

    def load_csv(self) -> None:
        dataframe : pandas.DataFrame = pandas.read_csv(self.filename)
        self.load_data(dataframe)
        
    def load_data(self, data : List[DataStoreRecord] | pandas.DataFrame) -> None:
        if hasattr(data, 'to_dict'):
            data = data.to_dict('records')
        self.data = data

    def get_dataframe(
        self, predicate: Any = None, fields: Optional[List[str]] = None
    ) -> pandas.DataFrame:
        if not self.data:
            raise DataStoreError("DataStore is empty")
        if predicate or fields:
            data = self._filter_data(predicate, fields)
        else:
            data = self.data
        rv = pandas.DataFrame(data)
        return rv

    def filter(
        self, predicate: Any = None, fields: Optional[List[str]] = None
    ) -> DataStore:
        if not self.data:
            raise DataStoreError("DataStore is empty")
        if predicate or fields:
            data = self._filter_data(predicate, fields)
        else:
            data = self.data
        rv = DataStore()
        rv.load_data(data)
        return rv

    def _filter_data(self, predicate: Any, fields: List[str]) -> List[DataStoreRecord]:
        """
        Inputdata is a list of dictionaries, they are filtered and the resulting list of dictionaries is returned.
        predicate is a Python expression returning True or False, if True the record is output.
        fields is a list of fieldnames to include in the output,
        use namefield=field to obtain field name from namefield
        """
        rv = []
        for record in self.data:
            nsrecord = dict(record) # shallow copy
            nsrecord["record"] = nsrecord
            if predicate == None or eval(predicate, nsrecord):
                if fields:
                    entry = dict()
                    for k in fields:
                        if "=" in k:
                            newk, oldk = k.split("=")
                            if "." in newk:
                                # Use field1.field2=field notation
                                newk1, newk2 = newk.split(".")
                                if not newk1 in record:
                                    continue
                                if not newk2:
                                    newk = record[newk1] + "." + oldk
                                else:
                                    if not newk2 in record:
                                        continue
                                    newk = record[newk1] + "." + record[newk2]
                            else:
                                if not newk in record:
                                    continue
                                newk = record[newk]
                            if not newk:
                                print(f'Warning: "{k}" produced no value for {record}', file=sys.stderr)
                        else:
                            newk = oldk = k

                        if oldk in record:
                            entry[newk] = record[oldk]
                else:
                    entry = record
                rv.append(entry)
        return rv

    def save(self) -> None:
        if not self.data:
            raise DataStoreError("DataStore is empty")
        assert self.filename
        if self.filename.endswith(".json"):
            self.save_json()
        elif self.filename.endswith(".csv"):
            self.save_csv()
        else:
            raise DataStoreError(f"Don't know how to save {self.filename}")

    def save_json(self) -> None:
        data = dict(
            metadata=self.annotator.to_dict(),
            data=self.data
        )
        json.dump(data, open(self.filename, "w"), indent="\t")

    def save_csv(self) -> None:
        pd = self.get_dataframe()
        pd.to_csv(self.filename, index=False)

    def find_first_record(self, predicate : Any, descr : str) -> DataStoreRecord:
        if not self.data:
            raise DataStoreError("DataStore is empty")
        if type(predicate) == type(str)and not self.debug:
            predicate = compile(predicate, "<string>", "eval")
        for record in self.data:
            nsrecord = dict(record) # shallow copy
            nsrecord["record"] = nsrecord
            if predicate == None or eval(predicate, nsrecord):
                return record
        raise DataStoreError(f"missing {descr}, predicate: {repr(predicate)}")
        
    def find_all_records(self, predicate : Any, descr : str) -> List[DataStoreRecord]:
        if not self.data:
            raise DataStoreError("DataStore is empty")
        if type(predicate) == type(str) and not self.debug:
            predicate = compile(predicate, "<string>", "eval")
        rv = []
        for record in self.data:
            nsrecord = dict(record) # shallow copy
            nsrecord["record"] = nsrecord
            if predicate == None or eval(predicate, nsrecord):
                rv.append(record)
        if not rv:
            raise DataStoreError(f"missing {descr}")
        return rv

    def sort(self, key: Callable) -> None:
        if not self.data:
            raise DataStoreError("DataStore is empty")
        self.data.sort(key=key)
