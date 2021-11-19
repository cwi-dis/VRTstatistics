import sys
import os
import json
import time
import types
import csv

def main():
    if len(sys.argv) < 4:
        print(f'Usage: {sys.argv[0]} input-json output-json-or-csv predicate [field [...]]')
        sys.exit(1)
    inputfile = sys.argv[1]
    outputfile = sys.argv[2]
    predicate = sys.argv[3]
    fields = sys.argv[4:]
    predicate = compile(predicate, '<string>', 'eval')
    ok = filter_files(inputfile, outputfile, predicate, fields)
    sys.exit(0 if ok else 1)
    
def filter_files(inputfile, outputfile, predicate, fields):
    """
    Filter inputfile to outputfile (which can be CSV or JSON).
    predicate is a Python expression returning True or False, if True the record is output.
    fields is a list of fieldnames to include in the output, 
    use namefield=field to obtain field name from namefield
    """
    inputdata = json.load(open(inputfile, 'r'))
    outputdata = filter_data(inputdata, predicate, fields)
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
    
def filter_data(inputdata, predicate, fields):
    """
    Inputdata is a list of dictionaries, they are filtered and the resulting list of dictionaries is returned.
    predicate is a Python expression returning True or False, if True the record is output.
    fields is a list of fieldnames to include in the output, 
    use namefield=field to obtain field name from namefield
    """
    rv = []
    for record in inputdata:
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
    
if __name__ == '__main__':
    main()
    
        