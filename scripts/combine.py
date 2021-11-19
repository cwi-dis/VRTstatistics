import sys
import os
import json
import time
import types
import csv

def main():
    if len(sys.argv) != 4:
        print(f'Usage: {sys.argv[0]} senderjson receiverjson outputjson')
        sys.exit(1)
    senderfile = sys.argv[1]
    receiverfile = sys.argv[2]
    outputfile = sys.argv[3]
    ok = combine_files(senderfile, receiverfile, outputfile)
    sys.exit(0 if ok else 1)
    
def combine_files(senderfile, receiverfile, outputfile):
    """
    Combine sender and receiver json files into single file.
    Session timestamps (relative to start of session), sender/receiver role are added to each record.
    Records are sorted by timstamp.
    """
    senderdata = json.load(open(senderfile, 'r'))
    receiverdata = json.load(open(receiverfile, 'r'))
    outputdata = combine_data(senderdata, receiverdata)
    json.dump(outputdata, open(outputfile, 'w'), indent='\t')
    return True
    
def combine_data(senderdata, receiverdata):
    """
    Senderdata and receiverdata are lists of dictionaries, they are combined and sorted and the result is returned.
    Session timestamps (relative to start of session), sender/receiver role are added to each record.
    Records are sorted by timstamp.
    """
    #
    # Find session ID and start time.
    #
    session_sender = find_session_id(senderdata)
    session_receiver = find_session_id(receiverdata)
    if session_sender != session_receiver:
        raise RuntimeError(f"sender has session {session_sender} and receiver has {session_receiver}")
    session_start_time_sender = find_session_start_time(senderdata)
    session_start_time_receiver = find_session_start_time(receiverdata)
    session_start_time = min(session_start_time_sender, session_start_time_receiver)
    #
    # Adjust data lists with session timestamps and roles
    #
    senderdata = adjust_time_and_role(senderdata, session_start_time, 'sender')
    receiverdata = adjust_time_and_role(receiverdata, session_start_time, 'receiver')
    #
    # Combine and sort
    #
    alldata = senderdata + receiverdata
    alldata.sort(key=lambda r : r['sessiontime'])
    return alldata

def find_session_id(data):
    for r in data:
        if not 'starting' in r or r['component'] != 'OrchestratorController': continue
        return r['sessionId']
    raise RuntimeError('missing session start')
    
def find_session_start_time(data):
    if False:
        # This would return session creation time. Start time is better.
        for r in data:
            if r['component'] == 'OrchestratorController' and r.get('starting') == 1:
                return r['orchtime']
    for r in data:
        if r['component'] == 'SessionPlayerManager':
            return r['orchtime']
    raise RuntimeError("missing SessionPlayerManager record to indicate session start")
    return None
    
def adjust_time_and_role(data, starttime, role):
    rv = []
    for r in data:
        newrecord = dict(r)
        if 'orchtime' in r:
            newrecord['sessiontime'] = r['orchtime'] - starttime
        else:
            continue # Delete records before start-of-session
        newrecord['role'] = role
        rv.append(newrecord)
    return rv
    
if __name__ == '__main__':
    main()
    
        