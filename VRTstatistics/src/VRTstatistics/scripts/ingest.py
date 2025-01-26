import sys
import os
import argparse
import json

from ..datastore import DataStore
from ..annotator import combine
from ..runner import Runner

verbose = True

def main():
    parser = argparse.ArgumentParser(description="Run a test, or ingest results")
    parser.add_argument("-d", "--destdir", help="directory to store results (default: current directory)")
    parser.add_argument("-a", "--annotator", metavar="ANN", help="Annotator to use for symbolic naming of records")
    parser.add_argument("-r", "--run", action="store_true", help="Run the test (default: only ingest data from an earlier run)")
    parser.add_argument("-C", "--vrtconfig", action="store", metavar="CONFIGFILE", help="Upload and use CONFIGFILE when running")
    parser.add_argument("--norusage", action="store_true", help="Do not try to get resource usage statistics logfiles")
    parser.add_argument("--nolog", action="store_true", help="Do not try to get Unity Player logfiles")
    parser.add_argument("--nofetch", action="store_true", help="Don't fetch log file but reuse earlier ones")
    parser.add_argument("-c", "--config", metavar="FILE", help="Use host configuration from FILE (json)")
    parser.add_argument("--writeconfig", metavar="FILE", help="Save default host configuration to FILE (json) and exit")
    parser.add_argument("--pausefordebug", action="store_true", help="Wait for a newline after start (so you can attach a debugger)")
    parser.add_argument("sender", help="Sender hostname")
    parser.add_argument("receiver", help="Receiver hostname")
    args = parser.parse_args()
    if args.pausefordebug:
        sys.stderr.write(f"Attach debugger to pid={os.getpid()}. Press return to continue - ")
        sys.stderr.flush()
        sys.stdin.readline()
    if args.writeconfig:
        json.dump(Runner.runnerConfig, open(args.writeconfig, "w"), indent=4)
        sys.exit(0)
    sys.stdout.write(f"working dir: {os.getcwd()}\n")
    sys.stdout.write(f"command line: {' '.join(sys.argv)}\n")
    if args.config:
        Runner.load_config(args.config)

    if args.destdir:
        destdir = args.destdir
    else:
        destdir = os.getcwd()

    if not os.path.exists(destdir):
        os.mkdir(destdir)
    
    sender = None
    receiver = None
    if args.run or not args.nofetch:
        sender = Runner(args.sender)
        receiver = Runner(args.receiver)

    if args.run:
        assert sender
        assert receiver
        if args.vrtconfig:
            sender.run_with_config(args.vrtconfig)
            receiver.run_with_config(args.vrtconfig)
        else:
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
       
    sender_stats = os.path.join(destdir, "sender.log")
    receiver_stats = os.path.join(destdir, "receiver.log")
    combined = os.path.join(destdir, "combined.json")
    sender_logfile = os.path.join(destdir, "sender-unity-log.txt")
    receiver_logfile = os.path.join(destdir, "receiver-unity-log.txt")
   
    if not args.nofetch:
        assert sender
        assert receiver
        if not args.nolog:
            sender.get_log(sender_logfile)
            receiver.get_log(receiver_logfile)
        
        sender.get_stats(sender_stats)
        receiver.get_stats(receiver_stats)
        if not args.norusage:

            sender_rusagefile = os.path.join(destdir, "sender-rusage.log")
            receiver_rusagefile = os.path.join(destdir, "receiver-rusage.log")

            sender.get_remotefile("rusage.log", sender_rusagefile)
            receiver.get_remotefile("rusage.log", receiver_rusagefile)
            #
            # Bit of a hack: we append resource usage to stats, so ts mapping is done correctly.
            #
            open(sender_stats, 'a').write(open(sender_rusagefile).read())
            open(receiver_stats, 'a').write(open(receiver_rusagefile).read())

    senderdata = DataStore(sender_stats)
    receiverdata = DataStore(receiver_stats)

    senderdata.load()
    receiverdata.load()

    outputdata = DataStore(combined)
    ok = combine(args.annotator, senderdata, receiverdata, outputdata)
    outputdata.save()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
