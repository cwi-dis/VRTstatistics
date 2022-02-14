import sys

from ..datastore import DataStore, DataStoreRecord, combine

def main():
    if len(sys.argv) != 4:
        print(f'Usage: {sys.argv[0]} senderjson receiverjson outputjson')
        sys.exit(1)
    senderdata = DataStore(sys.argv[1])
    senderdata.load()
    receiverdata = DataStore(sys.argv[2])
    receiverdata.load()
    outputdata = DataStore(sys.argv[3])
    ok = combine(senderdata, receiverdata, outputdata)
    outputdata.save()
    sys.exit(0 if ok else 1)
    
if __name__ == '__main__':
    main()
    
        
