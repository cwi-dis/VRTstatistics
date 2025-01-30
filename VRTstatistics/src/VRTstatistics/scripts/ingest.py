import sys
import os
import argparse

from ..datastore import DataStore
from ..annotator import combine
from VRTrun import Session

verbose = True

def main():
    parser = argparse.ArgumentParser(description="Run a test, or ingest results")
    parser.add_argument("-a", "--annotator", metavar="ANN", help="Annotator to use for symbolic naming of records")
    parser.add_argument("--norun", metavar="DIR", help="Don't run the test, only ingest data from an earlier run)")
    parser.add_argument("--pausefordebug", action="store_true", help="Wait for a newline after start (so you can attach a debugger)")
    args = parser.parse_args()
    if args.pausefordebug:
        sys.stderr.write(f"Attach debugger to pid={os.getpid()}. Press return to continue - ")
        sys.stderr.flush()
        sys.stdin.readline()

    # Check that we have either a config or hosts
    configdir = "./config"
    if not os.path.exists(configdir):
        print(f"{parser.prog}: Error: config directory {args.config} does not exist", file=sys.stderr)
        sys.exit(1)

    sessionconfig = Session.load_config(configdir)

    #
    # First we run the session (if needed)
    #
    if args.norun:
        workdir = args.norun
    else:

        workdir = Session.invent_workdir()

        session = Session(sessionconfig, configdir, workdir, verbose=verbose)

        session.start()

        session.run()

        sts = session.wait()

        session.receive_results()

        if sts != 0:
            print(f"{parser.prog}: Error: session failed with status {sts}", file=sys.stderr)
            return sts

    sender_stats_filename = os.path.join(workdir, "sender", "stats.log")
    receiver_stats_filename = os.path.join(workdir, "receiver", "stats.log")
    combined_filename = os.path.join(workdir, "combined.json") 
    senderdata = DataStore(sender_stats_filename)
    receiverdata = DataStore(receiver_stats_filename)

    senderdata.load()
    receiverdata.load()

    outputdata = DataStore(combined_filename)
    ok = combine(args.annotator, senderdata, receiverdata, outputdata)
    outputdata.save()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
