import sys
import urllib.parse
import subprocess
import requests
import threading
from typing import Optional

from .runnerconfig import defaultRunnerConfig

__all__ = ["Runner", "RunnerServerPort"]

RunnerServerPort = 5001
RunnerArgs = dict


class Runner:
    host: str
    user: str
    statPath: str
    verbose = True
    runnerConfig = defaultRunnerConfig

    @classmethod
    def load_config(cls, filename : str) -> None:
        assert False

    def __init__(self, url: str, config: Optional[RunnerArgs] = None) -> None:
        if ":" in url:
            parsed = urllib.parse.urlparse(
                self.url, scheme="ssh", allow_fragments=False
            )
            assert parsed.scheme == "ssh"
            assert parsed.hostname
            assert not parsed.port
            assert not parsed.password
            assert not parsed.query
            self.host = parsed.hostname
            self.user = parsed.username
        elif "@" in url:
            self.user, self.host = url.split("@")
        else:
            self.host = url
            self.user = ""
        if not config:
            config = self.runnerConfig[self.host]
        if not self.user:
            self.user = config["user"]
        self.statPath = config["statPath"]
        self.exePath = config.get("exePath")
        self.exeArgs = config.get("exeArgs", [])
        self.useSsh = config.get("useSsh", False)
        self.running = None

    def get_stats(self, filename):
        if self.user:
            scpPath = f"{self.user}@{self.host}:{self.statPath}"
        else:
            scpPath = f"{self.host}:{self.statPath}"
        cmd = ["scp", scpPath, filename]
        if self.verbose:
            print("+", " ".join(cmd), file=sys.stderr)
        subprocess.run(cmd)

    def run(self) -> None:
        assert not self.running
        if self.useSsh:
            self.running = self.run_ssh()
        else:
            self.running = threading.Thread(target=self.run_server_thread)
            self.running.start()

    def wait(self) -> int:
        assert self.running
        if self.useSsh:
            rv = self.running.wait()
        else:
            self.running.join()
            rv = self.status_code
        return rv

    def run_ssh(self) -> subprocess.Popen:
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
    
    def run_server_thread(self):
        if not self.exePath:
            raise RuntimeError(f"No exePath for {self.host}")
        cmd = [self.exePath] + self.exeArgs
        url = f"http://{self.host}:{RunnerServerPort}/run"
        if self.verbose:
            print(f"+ POST {url} {cmd}", file=sys.stderr)
        response = requests.post(url, json=cmd)
        print(response.text)
        self.status_code = response.status_code if response.status_code != 200 else 0
