import sys
import subprocess
import requests
import threading
import socket
import json
from typing import Optional, List, Any, cast, Union

from .runnerconfig import defaultRunnerConfig

__all__ = ["Runner", "RunnerServerPort"]

RunnerServerPort = 5001
RunnerArgs = dict[str, Any]


class Runner:
    host: str
    user: str
    statPath: str
    logPath: str
    exePath: str
    exeArgs : List[str]
    useSsh : bool
    running : Any
    verbose = True
    runnerConfig : dict[str, dict[str, Union[str, bool]]] = defaultRunnerConfig
    mdnsWorkaround = True

    @classmethod
    def load_config(cls, filename : str) -> None:
        cls.runnerConfig = json.load(open(filename))

    def __init__(self, machine: str, config: Optional[RunnerArgs] = None) -> None:
        self.host = machine
        if not config:
            config = self.runnerConfig.get(self.host)
            if not config:
                raise RuntimeError(f"Host key '{self.host}' not found in VRTstatistics configuration")
        self.user = config["user"]
        if "host" in config:
            self.host = config["host"]
        if self.mdnsWorkaround and ".local" in self.host:
            try:
                ip = socket.gethostbyname(self.host)
            except socket.gaierror:
                print(f"Cannot lookup '{self.host}'")
                raise
            if self.verbose:
                print(f'+ lookup {self.host} -> {ip}')
                self.host = ip
        self.statPath = config["statPath"]
        self.logPath = config["logPath"]
        self.exePath = cast(str, config.get("exePath"))
        self.exeArgs = config.get("exeArgs", [])
        self.useSsh = config.get("useSsh", False)
        self.running = None

    def get_log(self, filename : str) -> None:
        self.get_remotefile(self.logPath, filename)

    def get_stats(self, filename : str) -> None:
        self.get_remotefile(self.statPath, filename)

    def get_remotefile(self, remotepath : str, filename : str) -> None:
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

    def put_file(self, filename : str, data : str) -> str:
        if self.useSsh:
            raise RuntimeError("put_file not implemented over ssh")
        url = f"http://{self.host}:{RunnerServerPort}/putfile"
        if self.verbose:
            print(f"+ POST {url} filename={filename} data=...", file=sys.stderr)
        request_arg = {'filename' : filename, 'data' : data}
        r = requests.post(url, json=request_arg)
        rv = r.json()
        if self.verbose:
            print(f'- POST {url} -> {rv}')
        return rv['fullpath']

    def run(self, additionalArgs : Optional[List[str]] = None) -> None:
        assert self.running == None
        if self.useSsh:
            self.running = self._run_ssh(additionalArgs)
        else:
            self.running = threading.Thread(target=self._run_server_thread, args=(additionalArgs,))
            self.running.start()

    def wait(self) -> int:
        assert self.running != None
        if self.useSsh:
            rv = self.running.wait()
        else:
            self.running.join()
            rv = self.status_code
        return rv

    def _run_ssh(self, additionalArgs : Optional[List[str]] = None) -> subprocess.Popen:
        if not self.exePath:
            raise RuntimeError(f"No exePath for {self.host}")
        if self.user:
            sshHost = f"{self.user}@{self.host}"
        else:
            sshHost = self.host
        cmd = ["ssh", sshHost, self.exePath] + self.exeArgs
        if additionalArgs:
            cmd += additionalArgs
        if self.verbose:
            print("+", " ".join(cmd), file=sys.stderr)
        return subprocess.Popen(cmd)
    
    def _run_server_thread(self, additionalArgs : Optional[List[str]] = None):
        if not self.exePath:
            raise RuntimeError(f"No exePath for {self.host}")
        cmd = [self.exePath] + self.exeArgs
        if additionalArgs:
            cmd += additionalArgs
        url = f"http://{self.host}:{RunnerServerPort}/run"
        if self.verbose:
            print(f"+ POST {url} {cmd}", file=sys.stderr)
        response = requests.post(url, json=cmd)
        print(response.text)
        self.status_code = response.status_code if response.status_code != 200 else 0

    def run_with_config(self, configfile : str) -> None:
        configdata = open(configfile).read()
        remotepath = self.put_file("curconfig.json", configdata)
        self.run(["-vrt-config", remotepath])