import sys
import os
from datetime import datetime
from .runner import Runner
from .sessionconfig import SessionConfig
from typing import List, Optional

class Session:
    
    @staticmethod
    def invent_workdir() -> str:
        return datetime.now().strftime("run-%Y%m%d-%H%M")
    
    
    def __init__(self, config : SessionConfig, configdir : Optional[str], workdir : str, verbose : bool = False):
        self.config = config
        self.configdir = configdir
        self.workdir = workdir
        self.verbose = verbose
        self.runners : List[Runner] = []

    def start(self) -> None:
        if self.verbose:
            print("Creating processes...", file=sys.stderr)
        for machine_role, machine_address in self.config.get_machines():
            runner = Runner(machine_address, machine_role)
            self.runners.append(runner)

        if self.verbose:
            print("Loading configurations...", file=sys.stderr)
        for runner in self.runners:
            runner.start(self.workdir)
            if self.configdir:
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
            dirname = os.path.join(self.workdir, runner.role)
            runner.receive_results(self.workdir, dirname)
        pass
