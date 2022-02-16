import sys
import os
import argparse

from ..datastore import DataStore, DataStoreRecord
from ..annotator import combine
from ..runner import Runner

verbose = True

def main():
    parser = argparse.ArgumentParser(description="Run a test, or ingest results")
    parser.add_argument("-d", "--destdir", help="directory to store results (default: current directory)")
    parser.add_argument("-a", "--annotator", metavar="ANN", help="Annotator to use for symbolic naming of records")
    parser.add_argument("-r", "--run", action="store_true", help="Run the test (default: only ingest data from an earlier run)")
    parser.add_argument("-c", "--config", metavar="FILE", help="Use host configuration from FILE")
    parser.add_argument("sender", help="Sender hostname")
    parser.add_argument("receiver", help="Receiver hostname")
    args = parser.parse_args()
    if args.config:
        Runner.load_config(args.config)
    sender = Runner(args.sender)
    receiver = Runner(args.receiver)
    if args.destdir:
        destdir = args.destdir
    else:
        destdir = os.getcwd()

    if not os.path.exists(destdir):
        os.mkdir(destdir)
    
    if args.run:
        sender.run()
        receiver.run()
        if verbose:
            print("Waiting for processes to finish...", file=sys.stderr)
        sender_sts = sender.wait()
        if sender_sts != 0:
            print(f"Sender returned exit status {sender_sts}")
        receiver_sts = receiver.wait()
        if receiver_sts != 0:
            print(f"Receiver returned exit status {receiver_sts}")
        if sender_sts != 0 or receiver_sts != 0:
            sys.exit(1)
       
    sender_log = os.path.join(destdir, "sender.log")
    receiver_log = os.path.join(destdir, "receiver.log")
    combined = os.path.join(destdir, "combined.json")

    sender.get_stats(sender_log)
    receiver.get_stats(receiver_log)

    senderdata = DataStore(sender_log)
    receiverdata = DataStore(receiver_log)

    senderdata.load()
    receiverdata.load()

    outputdata = DataStore(combined)
    ok = combine(args.annotator, senderdata, receiverdata, outputdata)
    outputdata.save()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
