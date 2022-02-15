import sys
import os

from ..datastore import DataStore, DataStoreRecord, combine
from ..runner import Runner


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} sender receiver")
        sys.exit(1)
    sender = Runner(sys.argv[1])
    receiver = Runner(sys.argv[2])
    destdir = os.getcwd()

    if not os.path.exists(destdir):
        os.mkdir(destdir)

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
    ok = combine(senderdata, receiverdata, outputdata)
    outputdata.save()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
