import sys
import os
import json
import time
import types
import csv
from typing import Optional, Callable

StatisticsRecord = dict

class StatisticsDataStore:
    filename : str
    data : list[StatisticsRecord]
    session_id : Optional[str]
    session_start_time : Optional[float]
    session_desync : Optional[float]

    def __init__(self, filename : str) -> None:
        self.filename = filename
        self.data = []
        self.session_id = None
        self.session_start_time = None
        self.session_desync = None
        
    def load(self) -> None:
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
        assert False

    def load_data(self, data) -> None:
        self.data = data

    def save(self) -> None:
        if self.filename.endswith(".json"):
            self.save_json()
        else:
            raise RuntimeError(f"Don't know how to save {self.filename}")

    def save_json(self) -> None:
        json.dump(self.data, open(self.filename, 'w'), indent='\t')


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

def main():
    if len(sys.argv) != 4:
        print(f'Usage: {sys.argv[0]} senderjson receiverjson outputjson')
        sys.exit(1)
    senderdata = StatisticsDataStore(sys.argv[1])
    senderdata.load()
    receiverdata = StatisticsDataStore(sys.argv[2])
    receiverdata.load()
    outputdata = StatisticsDataStore(sys.argv[3])
    ok = combine_files(senderdata, receiverdata, outputdata)
    outputdata.save()
    sys.exit(0 if ok else 1)
    
def combine_files(senderdata : StatisticsDataStore, receiverdata : StatisticsDataStore, outputdata : StatisticsDataStore) -> bool:
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
    
    
if __name__ == '__main__':
    main()
    
        
