from __future__ import annotations
import sys
import json
from typing import Optional, List, Any, cast, Dict, Union
from types import CodeType
from .parser import StatsFileParser
import pandas

__all__ = ["DataStoreRecord", "DataStore", "DataStoreError"]

class DataStoreError(RuntimeError):
    pass

type DataStoreRecord = dict[str, Any]
"""
A single entry in a DataStore.
"""

type Predicate = Union[str, CodeType]
"""
A Predicate is a boolean Python expression, evaluated with a DataStoreRecord as its globals.

Field names can be used in the expression, and the special name "record" signifies the whole record.
"""

type FieldSpecifier = str
"""
A FieldSpecifier specifies now an input record field is mapped to an output record field.

The simplest form is just an identifier: the field with that name will be in the output recurd under the same name.
The form "out=in" will take the value of input field "out" and use that as the output record field name for the value of "in".
The form "out1.out2=in" will take the value of input field "out1" and "out2", concatenate them with a "." and use that as the output record field name for the value of "in".
The form "out1.=in" will take the value of input field "out1", concatenate that with a "." and the name of the input field, and use that as the output record field name for the value of "in".

"""
class DataStore:
    """
    All data obtained from a single run.

    Can be loaded from various file formats (and saved to it).
    Can be filtered and searched.
    Can be accessed as Pandas DataFrame.
    """
    debug = True
    verbose = True

    filename: Optional[str]
    data: list[DataStoreRecord]
    annotator : Any
   
    def __init__(self, filename: Optional[str] = None, filename2: Optional[str] = None) -> None:
        """
        Create a DataStore, does not load anything yet.
        
        :param filename: The filename to load from (and save to). Can be json, csv or stats-style log.
        :type filename: Optional[str]
        :param filename2: Optional second file to load, for some filetypes.
        :type filename2: Optional[str]
        """
        self.filename = filename
        self.filename2 = filename2
        self.data = []
        self.annotator = None

    def load(self) -> None:
        """
        Load the datastore from the filename(s) passed during creation
        """
        assert self.filename
        if self.filename == "-":
            pass
        elif self.filename.endswith(".json"):
            self._load_json()
        elif self.filename.endswith(".log"):
            self._load_log()
        elif self.filename.endswith(".csv"):
            self._load_csv()
        else:
            raise DataStoreError(f"Don't know how to load {self.filename}")

    def _load_json(self) -> None:
        assert self.filename
        assert not self.filename2
        data = json.load(open(self.filename, "r"))
        metadata = None
        if type(data) != type([]):
            metadata = data["metadata"]
            data = data["data"]
        self.data = data
        if metadata:
            from .annotator import deserialize
            self.annotator = deserialize(self, metadata)

    def _load_log(self, nocheck : bool=False) -> None:
        assert self.filename
        parser = StatsFileParser(self.filename, self.filename2)
        self.data = parser.parse()
        if not nocheck:
            parser.check()

    def _load_csv(self) -> None:
        assert self.filename
        assert not self.filename2
        dataframe : pandas.DataFrame = pandas.read_csv(self.filename) # type: ignore
        self.load_data(dataframe)
        
    def load_data(self, data : List[DataStoreRecord] | pandas.DataFrame) -> None:
        """
        Load data from a list of DataStoreRecords or a pandas DataFrame
        :param data: The content to load into this DataStore
        :type data: List[DataStoreRecord] | pandas.DataFrame
        """
        if hasattr(data, 'to_dict'):
            df : pandas.DataFrame = cast(pandas.DataFrame, data)
            data = df.to_dict('records') # type: ignore
        self.data = cast(List[DataStoreRecord],data)

    def get_dataframe(
        self, predicate: Optional[Predicate] = None, fields: Optional[List[FieldSpecifier]] = None
    ) -> pandas.DataFrame:
        """
        Return the DataStore as a pandas DataFrame.
        
        :param predicate: A boolean predicate function. Only records that match this predicate are included in the output. If no predicate is specified all records are returned.
        :type predicate: Predicate
        :param fields: A list of fields wanted in the returned DataFrame records. If not specified all fields are included.
        :type fields: Optional[List[FieldSpecifier]]
        :return: The resultant DataFrame
        :rtype: DataFrame
        """
        if not self.data:
            raise DataStoreError("DataStore is empty")
        if predicate or fields:
            data = self._filter_data(predicate, fields)
        else:
            data = self.data
        rv = pandas.DataFrame(data)
        return rv

    def filter(
        self, predicate: Optional[Predicate] = None, fields: Optional[List[FieldSpecifier]] = None
    ) -> DataStore:
        """
        Return a copy of the DataStore, possibly after filtering.
        
        :param predicate: A boolean predicate function. Only records that match this predicate are included in the output. If no predicate is specified all records are returned.
        :type predicate: Predicate
        :param fields: A list of fields wanted in the returned DataStore records. If not specified all fields are included.
        :type fields: Optional[List[FieldSpecifier]]
        :return: The resultant DataStore
        :rtype: DataStore
        """
        if not self.data:
            raise DataStoreError("DataStore is empty")
        if predicate or fields:
            data = self._filter_data(predicate, fields)
        else:
            data = self.data
        rv = DataStore()
        rv.load_data(data)
        return rv

    def _filter_data(self, predicate: Any, fields: Optional[List[str]]) -> List[DataStoreRecord]:
        """
        Inputdata is a list of dictionaries, they are filtered and the resulting list of dictionaries is returned.
        predicate is a Python expression returning True or False, if True the record is output.
        fields is a list of fieldnames to include in the output,
        use namefield=field to obtain field name from namefield
        """
        rv : List[DataStoreRecord] = []
        for record in self.data:
            nsrecord = dict(record) # shallow copy
            nsrecord["record"] = nsrecord
            if predicate == None or eval(predicate, nsrecord):
                if fields:
                    entry : Dict[Any, Any] = dict()
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
        if len(rv) == 0:
            print(f"_filter_data: Warning: empty dataset for fields={fields}, predicate: {predicate}")
        return rv

    def save(self) -> None:
        """
        Save the DataStore.

        Only works for .json and .csv filenames, stats-style .log format is readonly.
        """
        if not self.data:
            raise DataStoreError("DataStore is empty")
        assert self.filename
        if self.filename.endswith(".json"):
            self._save_json()
        elif self.filename.endswith(".csv"):
            self._save_csv()
        else:
            raise DataStoreError(f"Don't know how to save {self.filename}")

    def _save_json(self) -> None:
        data = dict(
            metadata=self.annotator.to_dict(),
            data=self.data
        )
        assert self.filename
        json.dump(data, open(self.filename, "w"), indent="\t")

    def _save_csv(self) -> None:
        pd = self.get_dataframe()
        pd.to_csv(self.filename, index=False)

    def find_first_record(self, predicate : Predicate, descr : str) -> DataStoreRecord:
        """
        Return the first record in the DataStore that matches a predicate.
        
        :param predicate: The predicate
        :type predicate: Predicate
        :param descr: Human-readable description of what we are searching for, for error messages only.
        :type descr: str
        :return: The first record matching the predicate
        :rtype: DataStoreRecord
        """
        if not self.data:
            raise DataStoreError("DataStore is empty")
        if type(predicate) == str and not self.debug:
            predicate = compile(predicate, "<string>", "eval")
        for record in self.data:
            nsrecord = dict(record) # shallow copy
            nsrecord["record"] = nsrecord
            if eval(predicate, nsrecord):
                return record
        raise DataStoreError(f"missing {descr}. No record found for predicate: {repr(predicate)}")
        
    def find_all_records(self, predicate : Predicate, descr : str) -> List[DataStoreRecord]:
        """
        Return all records in the DataStore that match a predicate.
        
        :param predicate: The predicate
        :type predicate: Predicate
        :param descr: Human-readable description of what we are searching for, for error messages only.
        :type descr: str
        :return: All records matching the predicate
        :rtype: List[DataStoreRecord]
        """
        if not self.data:
            raise DataStoreError("DataStore is empty")
        if type(predicate) == str and not self.debug:
            predicate = compile(predicate, "<string>", "eval")
        rv : List[DataStoreRecord] = []
        for record in self.data:
            nsrecord = dict(record) # shallow copy
            nsrecord["record"] = nsrecord
            if eval(predicate, nsrecord):
                rv.append(record)
        if not rv:
            raise DataStoreError(f"missing {descr}. No record found for predicate: {predicate}.")
        return rv

    def sort(self, key: Any) -> None:
        """
        Sort the data in-place.

        :param key: Standard sort() ordering function.
        :type key: Any
        """
        if not self.data:
            raise DataStoreError("DataStore is empty")
        self.data.sort(key=key)
