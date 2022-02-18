import sys
import urllib.parse
import subprocess
import requests
import threading
from typing import Optional, List

from .runnerconfig import defaultRunnerConfig

__all__ = ["Runner", "RunnerServerPort"]

RunnerServerPort = 5001
RunnerArgs = dict


class Runner:
    host: str
    user: str
    statPath: str
    logPath: str
    exePath: str
    exeArgs : List[str]
    useSsh : bool
    verbose = True
    runnerConfig = defaultRunnerConfig

    @classmethod
    def load_config(cls, filename : str) -> None:
        assert False

    def __init__(self, machine: str, config: Optional[RunnerArgs] = None) -> None:
        self.host = machine
        if not config:
            config = self.runnerConfig[self.host]
        self.user = config["user"]
        if "host" in config:
            self.host = config["host"]
        self.statPath = config["statPath"]
        self.logPath = config["logPath"]
        self.exePath = config.get("exePath")
        self.exeArgs = config.get("exeArgs", [])
        self.useSsh = config.get("useSsh", False)
        self.running = None

    def get_log(self, filename : str) -> None:
        self._get_remotefile(self.logPath, filename)

    def get_stats(self, filename : str) -> None:
        self._get_remotefile(self.statPath, filename)

    def _get_remotefile(self, remotepath : str, filename : str) -> None:
        if self.useSsh:
            self._get_remotefile_ssh(remotepath, filename)
        else:
            self._get_remotefile_server(remotepath, filename)

    def _get_remotefile_ssh(self, remotepath : str, filename : str) -> None:
        if self.user:
            scpPath = f"{self.user}@{self.host}:{remotepath}"
        else:
            scpPath = f"{self.host}:{remotepath}"
        cmd = ["scp", scpPath, filename]
        if self.verbose:
            print("+", " ".join(cmd), file=sys.stderr)
        subprocess.run(cmd)

    def _get_remotefile_server(self, remotepath : str, filename : str) -> None:
        url = f"http://{self.host}:{RunnerServerPort}/getfile"
        if self.verbose:
            print(f"+ GET {url} fullpath={remotepath}")
        r = requests.get(url, json={'fullpath' : remotepath})
        r.raise_for_status()
        result = r.text
        open(filename, 'w').write(result)
        if self.verbose:
            print(f"- GET {url} filename={filename} size={len(result)}")

    def put_file(self, filename : str, data : str) -> None:
        if self.useSsh:
            raise RuntimeError("put_file not implemented over ssh")
        url = f"http://{self.host}:{RunnerServerPort}/putfile"
        if self.verbose:
            print(f"+ POST {url} filename={filename} data=...", file=sys.stderr)
        data = {'filename' : filename, 'data' : data}
        r = requests.post(url, json=data)
        rv = r.json
        if self.verbose:
            print(f'- POST {url} -> {rv}')
        return rv['fullpath']

    def run(self) -> None:
        assert not self.running
        if self.useSsh:
            self.running = self._run_ssh()
        else:
            self.running = threading.Thread(target=self._run_server_thread)
            self.running.start()

    def wait(self) -> int:
        assert self.running
        if self.useSsh:
            rv = self.running.wait()
        else:
            self.running.join()
            rv = self.status_code
        return rv

    def _run_ssh(self) -> subprocess.Popen:
        if not self.exePath:
            raise RuntimeError(f"No exePath for {self.host}")
        if self.user:
            sshHost = f"{self.user}@{self.host}"
        else:
            sshHost = self.host
        cmd = ["ssh", sshHost, self.exePath] + self.exeArgs
        if self.verbose:
            print("+", " ".join(cmd), file=sys.stderr)
        return subprocess.Popen(cmd)
    
    def _run_server_thread(self):
        if not self.exePath:
            raise RuntimeError(f"No exePath for {self.host}")
        cmd = [self.exePath] + self.exeArgs
        url = f"http://{self.host}:{RunnerServerPort}/run"
        if self.verbose:
            print(f"+ POST {url} {cmd}", file=sys.stderr)
        response = requests.post(url, json=cmd)
        print(response.text)
        self.status_code = response.status_code if response.status_code != 200 else 0
