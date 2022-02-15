import sys
import os
import json
import time
import types
import csv
from typing import Callable, List
from ..datastore import DataStore

def main():
    if len(sys.argv) < 4:
        print(f'Usage: {sys.argv[0]} datastore output-json-or-csv predicate [field [...]]')
        sys.exit(1)
    datastore = DataStore(sys.argv[1])
    datastore.load()
    outputfile = sys.argv[2]
    predicate = sys.argv[3]
    fields = sys.argv[4:]
    predicate = compile(predicate, '<string>', 'eval')
    output = datastore.filter(predicate, fields)
    output.filename = outputfile
    output.save()
    sys.exit(0)
    
def filter_files(datastore: DataStore, outputfile : str, predicate : Callable, fields : List[str]):
    """
    Filter inputfile to outputfile (which can be CSV or JSON).
    predicate is a Python expression returning True or False, if True the record is output.
    fields is a list of fieldnames to include in the output, 
    use namefield=field to obtain field name from namefield
    """
    output : DataStore = datastore.filter(predicate, fields)
    output.filename = outputfile
    output.save()
    if False:
        base, ext = os.path.splitext(outputfile)
        if ext.lower() == '.json':
            json.dump(outputdata, open(outputfile, 'w'), indent='\t')
        elif ext.lower() == '.csv':
            # Determine key order in CSV file. First all the explicitly mentioned keys
            allkeys = []
            for f in fields:
                if not '=' in f:
                    allkeys.append(f)
            # Next, the rest of the keys, but we will sort them first.
            morekeys = []
            for record in outputdata:
                for k in record.keys():
                    if not k in allkeys and not k in morekeys:
                        morekeys.append(k)
            morekeys.sort()
            allkeys = allkeys + morekeys
            with open(outputfile, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, allkeys)
                writer.writeheader()
                for record in outputdata:
                    writer.writerow(record)
        else:
            print(f'Unknown file extension {ext}', file=sys.stderr)
            return False
    return True
    
    
if __name__ == '__main__':
    main()
    
        