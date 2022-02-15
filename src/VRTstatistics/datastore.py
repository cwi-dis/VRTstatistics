from __future__ import annotations
import sys
import json
from typing import Optional, List, Callable, Any
from .parser import StatsFileParser
import pandas

__all__ = [
    "DataStoreRecord",
    "DataStore",
    "combine"
]

DataStoreRecord = dict

class DataStore:
    filename : str
    data : list[DataStoreRecord]
    session_id : Optional[str]
    session_start_time : Optional[float]
    session_desync : Optional[float]

    def __init__(self, filename : Optional[str] = None) -> None:
        self.filename = filename
        self.data = []
        self.session_id = None
        self.session_start_time = None
        self.session_desync = None
        
    def load(self) -> None:
        assert self.filename
        if self.filename == "-":
            pass
        elif self.filename.endswith(".json"):
            self.load_json()
        elif self.filename.endswith(".log"):
            self.load_log()
        else:
            raise RuntimeError(f"Don't know how to load {self.filename}")

    def load_json(self) -> None:
        self.data = [] if self.filename == '-' else json.load(open(self.filename, 'r'))
        
    def load_log(self) -> None:
        parser = StatsFileParser(self.filename)
        self.data = parser.parse()
        parser.check()

    def load_data(self, data) -> None:
        self.data = data

    def get_dataframe(self, predicate : Any = None, columns : Optional[List[str]] = None) -> pandas.DataFrame:
        if predicate or columns:
            data = self._filter_data
        else:
            data = self.data
        return pandas.DataFrame(data, columns=columns)

    def filter(self, predicate : Any = None, columns : Optional[List[str]] = None) -> DataStore:
        if predicate or columns:
            data = self._filter_data(predicate, columns)
        else:
            data = self.data
        rv = DataStore()
        rv.load_data(data)
        return rv

    def _filter_data(self, predicate : Any, fields : List[str]) -> List[DataStoreRecord]:
        """
        Inputdata is a list of dictionaries, they are filtered and the resulting list of dictionaries is returned.
        predicate is a Python expression returning True or False, if True the record is output.
        fields is a list of fieldnames to include in the output, 
        use namefield=field to obtain field name from namefield
        """
        rv = []
        for record in self.data:
            nsrecord = dict(record)
            nsrecord['record'] = nsrecord
            if eval(predicate, nsrecord):
                if fields:
                    entry = dict()
                    for k in fields:
                        if '=' in k:
                            newk, oldk = k.split('=')
                            if '.' in newk:
                                # Use field1.field2=field notation
                                newk1, newk2 = newk.split('.')
                                if not newk1 in record or not newk2 in record:
                                    continue
                                newk = record[newk1] + '.' + record[newk2]
                            else:
                                if not newk in record:
                                    continue
                                newk = record[newk]
                        else:
                            newk = oldk = k
                        
                        if oldk in record:
                            entry[newk] = record[oldk]
                else:
                    entry = record
                rv.append(entry)
        return rv

    def save(self) -> None:
        assert self.filename
        if self.filename.endswith(".json"):
            self.save_json()
        elif self.filename.endswith(".csv"):
            self.save_csv()
        else:
            raise RuntimeError(f"Don't know how to save {self.filename}")

    def save_json(self) -> None:
        json.dump(self.data, open(self.filename, 'w'), indent='\t')

    def save_csv(self) -> None:
        pd = self.get_dataframe()
        pd.to_csv(self.filename, index=False)

    def get_session_id(self) -> str:
        if self.session_id != None:
            return self.session_id
        for r in self.data:
            if not 'starting' in r or r['component'] != 'OrchestratorController': continue
            self.session_id = r['sessionId']
            return self.session_id
        raise RuntimeError('missing session start')
        
    def get_session_desync(self) -> int:
        if self.session_desync != None:
            return self.session_desync
        for r in self.data:
            if r['component'] == 'OrchestratorController' and 'localtime_behind_ms' in r:
                self.session_desync = r['localtime_behind_ms']
                return self.session_desync
        raise RuntimeError("Missing OrchestratorController time synchronization record")
            
    def get_session_start_time(self) -> float:
        if self.session_start_time != None:
            return self.session_start_time
        if False:
            # This would return session creation time. Start time is better.
            for r in data:
                if r['component'] == 'OrchestratorController' and r.get('starting') == 1:
                    return r['orchtime']
        for r in self.data:
            if r['component'] == 'SessionPlayerManager':
                self.session_start_time = r['orchtime']
                return self.session_start_time
        raise RuntimeError("missing SessionPlayerManager record to indicate session start")
        
    def adjust_time_and_role(self, starttime : float, role : str) -> None:
        self.session_start_time = starttime
        rv = []
        for r in self.data:
            newrecord = dict(r)
            if 'orchtime' in r:
                newrecord['sessiontime'] = r['orchtime'] - starttime
            else:
                continue # Delete records before start-of-session
            newrecord['role'] = role
            rv.append(newrecord)
        self.data = rv

    def sort(self, key : Callable) -> None:
        self.data.sort(key=key)

def combine(senderdata : DataStore, receiverdata : DataStore, outputdata : DataStore) -> bool:
    """
    Senderdata and receiverdata are lists of dictionaries, they are combined and sorted and the result is returned.
    Session timestamps (relative to start of session), sender/receiver role are added to each record.
    Records are sorted by timstamp.
    """
    #
    # Find session ID and start time.
    #
    session_start_time = None
    sender_desync = None
    receiver_desync = None

    session_sender = senderdata.get_session_id()
    session_start_time_sender = senderdata.get_session_start_time()
    session_start_time = session_start_time_sender
    sender_desync = senderdata.get_session_desync()
    #
    # Adjust data lists with session timestamps and roles
    #
    senderdata.adjust_time_and_role(session_start_time, 'sender')

    session_receiver = receiverdata.get_session_id()
    if session_sender != session_receiver:
        raise RuntimeError(f"sender has session {session_sender} and receiver has {session_receiver}")
    session_start_time_receiver = receiverdata.get_session_start_time()
    if abs(session_start_time_receiver-session_start_time_sender) > 1:
        print(f"Warning: different session start times, {abs(session_start_time_receiver-session_start_time_sender)} seconds apart: sender {session_start_time_sender} receiver {session_start_time_receiver}", file=sys.stderr)
    receiver_desync = receiverdata.get_session_desync()
    session_start_time = min(session_start_time_sender, session_start_time_receiver)
    #
    # Adjust data lists with session timestamps and roles
    #
    receiverdata.adjust_time_and_role(session_start_time, 'receiver')

    if abs(sender_desync) > 30 or abs(receiver_desync > 30):
        print(f'Warning: synchronization: sender {sender_desync}ms behind orchestrator', file=sys.stderr)
        print(f'Warning: synchronization: receiver {receiver_desync}ms behind orchestrator', file=sys.stderr)
    #
    # Combine and sort
    #
    outputdata.load_data(senderdata.data + receiverdata.data)
    outputdata.sort(key=lambda r : r['sessiontime'])
    return True
 