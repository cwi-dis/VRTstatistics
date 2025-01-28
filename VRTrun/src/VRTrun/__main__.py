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
    parser.add_argument("-d", "--destdir", help="directory to store results (default: current directory)")
    parser.add_argument("-r", "--run", action="store_true", help="Run the test (default: only ingest data from an earlier run)")
    parser.add_argument("--norusage", action="store_true", help="Do not try to get resource usage statistics logfiles")
    parser.add_argument("--nolog", action="store_true", help="Do not try to get Unity Player logfiles")
    parser.add_argument("--nofetch", action="store_true", help="Don't fetch log file but reuse earlier ones")
    parser.add_argument("-c", "--config", metavar="FILE", help="Use host configuration from FILE (json)")
    parser.add_argument("--writeconfig", metavar="FILE", help="Save default host configuration to FILE (json) and exit")
    parser.add_argument("--pausefordebug", action="store_true", help="Pause before starting to allow attaching a debugger")
    # xxxjack add machines
    
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

    configdir = "./config"
    workdir = datetime.now().strftime("run-%Y%m%d-%H%M")
    machines = json.load(open(os.path.join(configdir, "runconfig.json")))

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
