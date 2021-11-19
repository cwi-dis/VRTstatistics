import sys
import os
import json
import time

def main():
    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} logfile statsfile-or-dir')
        sys.exit(1)
    logfile = sys.argv[1]
    statsfile = sys.argv[2]
    ok = stats2json(logfile, statsfile)
    sys.exit(0 if ok else 1)
    
def stats2json(logfile, statsfile):
    """Convert raw logfile containing stats: lines to JSON file.
    If statsfile is an existing directory the filename will be the source
    filename with .json extension in stead of .log""" 
    # If output is a directory use logfile name but with .json extension
    if os.path.isdir(statsfile):
        fn = os.path.splitext(os.path.basename(logfile))[0]
        statsfile = os.path.join(statsfile, fn + '.json')
    data = extractstats(logfile, open(logfile))
    ok = checkstats(logfile, data)
    if ok:
        json.dump(data, open(statsfile, 'w'), indent='\t')
    return ok
        
def extractstats(ifname, ifp):
    rv = []
    localtime_epoch = None
    orchtime_epoch = None
    linenum = 0
    for line in ifp:
        linenum += 1
        line = line.strip()
        if not line.startswith('stats: '):
            continue
        line = line[7:]  # Remove the stats:
        entry = extractstats_single_new(line)
        #
        # See if we have info to allow conversion of timestamps already
        #
        if 'orchestrator_ntptime_ms' in entry:
            orch_time = entry['orchestrator_ntptime_ms'] / 1000.0
            orch_gmtime = time.gmtime(orch_time)
            orch_midnight_gmtime = time.struct_time((orch_gmtime.tm_year, orch_gmtime.tm_mon, orch_gmtime.tm_mday, 0, 0, 0, 0, 0, 0))
            orch_midnight = time.mktime(orch_midnight_gmtime)
            localtime_epoch = orch_midnight
            orchtime_epoch = orch_time - entry['ts']
        if localtime_epoch:
            entry['localtime'] = localtime_epoch + entry['ts']
        if orchtime_epoch:
            entry['orchtime'] = orchtime_epoch + entry['ts']
        rv.append(entry)
    return rv
    
def extractstats_single_new(line):
    """Extract new-style statistics from a single line"""
    entry = {}
    fields = line.split(',')
    for field in fields:
        field = field.strip()
        splitfield = field.split('=')
        k = splitfield[0]
        v = '='.join(splitfield[1:])
        # Try to convert v to natural value
        try:
            vi = int(v)
            v = vi
        except ValueError:
            try:
                vf = float(v)
                v = vf
            except ValueError:
                pass
        entry[k] = v
    return entry
        
def checkstats(ifname, data):
    ok = True
    startEntry = None
    stopEntry = None
    timeEntry = None
    for entry in data:
        if not entry['component'] == 'OrchestratorController': continue
        if 'starting' in entry:
            if startEntry:
                print(f'{ifname}: duplicate start of session')
                ok = False
            startEntry = entry
        if 'orchestrator_ntptime_ms' in entry:
            if timeEntry:
                print(f'{ifname}: duplicate session time-synchronization entry')
                ok = False
            timeEntry = entry
        if 'stopping' in entry:
            if stopEntry:
                print(f'{ifname}: duplicate end of session')
                ok = False
            stopEntry = entry
    if False and not startEntry:
        # Don't print this warning: the start entry is only printed for the initiator
        print(f'{ifname}: warning: missing start of session ')
    if not timeEntry:
        print(f'{ifname}: missing session time-synchronization entry')
        ok = False
    if not stopEntry:
        print(f'{ifname}: warning: missing end of session')
    if startEntry and stopEntry and startEntry['sessionId'] != stopEntry['sessionId']:
        print(f'{ifname}: session different between start and stop')
        ok = False
    return ok
            
if __name__ == '__main__':
    main()
