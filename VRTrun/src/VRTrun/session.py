import sys
import os
from .runner import Runner
from typing import List, Dict

class Session:
    def __init__(self, machines : List[str] | Dict[str, str], configdir : str, workdirname : str, verbose : bool = False):
        self.machines = machines
        self.configdir = configdir
        self.workdirname = workdirname
        self.verbose = verbose
        self.runners : List[Runner] = []

    def start(self) -> None:
        if self.verbose:
            print("Creating processes...", file=sys.stderr)
        for machine in self.machines:
            if type(machine) == str:
                machine_role = machine
                machine_address = machine
            else:
                machine_role = machine["role"]
                machine_address = machine["address"]
            runner = Runner(machine_address, machine_role)
            self.runners.append(runner)

        if self.verbose:
            print("Loading configurations...", file=sys.stderr)
        for runner in self.runners:
            runner.start(self.workdirname)
            runner.upload_config_dir(self.configdir, recursive=False)
            runner.upload_config_dir(os.path.join(self.configdir, runner.role), recursive=True)
            runner.send_config()



    def run(self) -> None:
        if self.verbose:
            print("Starting processes...", file=sys.stderr)
        for runner in self.runners:
            runner.run()

    def wait(self) -> int:
        if self.verbose:
            print("Waiting for processes to finish...", file=sys.stderr)
        # xxxjack it would be good to be able to abort the runners with control-C
        all_status = 0
        for runner in self.runners:
            sts = runner.wait()
            if self.verbose or sts != 0:
                print(f"Runner {runner.role} returned {sts}", file=sys.stderr)
            if sts != 0:
                all_status = sts
        return all_status

    def receive_results(self) -> None:
        if self.verbose:
            print("Fetching results...", file=sys.stderr)
        for runner in self.runners:
            runner.receive_results()
        pass
