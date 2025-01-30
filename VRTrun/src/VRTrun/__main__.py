import sys
import os
import argparse
import json
from typing import List
from datetime import datetime
from . import Runner, Session

verbose = True

def main():
    parser = argparse.ArgumentParser(description="Run a VR2Gather player session")
    parser.add_argument("--config", metavar="DIR", default="./config", help="Config directory to use (default: ./config)")
    parser.add_argument("--host", action="append", metavar="HOST", help="Don't use config but simply run on HOST. May be repeated")
    parser.add_argument("--pausefordebug", action="store_true", help="Pause before starting to allow attaching a debugger")
    # xxxjack add machines
    
    args = parser.parse_args()
    if args.pausefordebug:
        sys.stderr.write(f"Attach debugger to pid={os.getpid()}. Press return to continue - ")
        sys.stderr.flush()
        sys.stdin.readline()
    # Check that we have either a config or hosts
    if args.host:
        if os.path.exists(args.config):
            print(f"{parser.prog}: Error: don't use --host if a config directory exists", file=sys.stderr)
            sys.exit(1)
        configdir = None
        machines = args.host
    else:
        if not os.path.exists(args.config):
            print(f"{parser.prog}: Error: config directory {args.config} does not exist", file=sys.stderr)
            sys.exit(1)
        configdir = args.config
        machines = json.load(open(os.path.join(configdir, "runconfig.json")))

    workdir = datetime.now().strftime("run-%Y%m%d-%H%M")

    session = Session(machines, configdir, workdir, verbose=verbose)

    session.start()

    session.run()

    sts = session.wait()

    session.receive_results()

    return sts

       
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
    return 0

if __name__ == "__main__":
    main()
