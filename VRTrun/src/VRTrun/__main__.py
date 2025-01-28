import sys
import os
import argparse
import json
from typing import List
from datetime import datetime
from . import Runner

verbose = True

def main():
    parser = argparse.ArgumentParser(description="Run a VR2Gather player session")
    parser.add_argument("-d", "--destdir", help="directory to store results (default: current directory)")
    parser.add_argument("-r", "--run", action="store_true", help="Run the test (default: only ingest data from an earlier run)")
    parser.add_argument("-C", "--vrtconfig", action="store", metavar="CONFIGFILE", help="Upload and use CONFIGFILE when running")
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
    workdirname = datetime.now().strftime("run-%Y%m%d-%H%M")
    machines = json.load(open(os.path.join(configdir, "runconfig.json")))
    runners : List[Runner] = []
    if verbose:
        print("Creating processes...", file=sys.stderr)
    for machine in machines:
        if type(machine) == str:
            machine_role = machine
            machine_address = machine
        else:
            machine_role = machine["role"]
            machine_address = machine["address"]
        runner = Runner(machine_address, machine_role)
        runners.append(runner)

    if verbose:
        print("Loading configurations...", file=sys.stderr)
    for runner in runners:
        runner.start(workdirname)
        runner.load_config_dir(os.path.join(configdir, "default"))
        runner.load_config_dir(os.path.join(configdir, runner.role))
        runner.send_config()

    if verbose:
        print("Starting processes...", file=sys.stderr)
    for runner in runners:
        runner.run()

    if verbose:
        print("Waiting for processes to finish...", file=sys.stderr)
    # xxxjack it would be good to be able to abort the runners with control-C
    all_status = 0
    for runner in runners:
        sts = runner.wait()
        if verbose or sts != 0:
            print(f"Runner {runner.role} returned {sts}", file=sys.stderr)
        if sts != 0:
            all_status = sts

    if verbose:
        print("Fetching results...", file=sys.stderr)
    for runner in runners:
        runner.receive_results()

    return all_status
       
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
