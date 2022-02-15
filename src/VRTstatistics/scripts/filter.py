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
    
if __name__ == '__main__':
    main()
