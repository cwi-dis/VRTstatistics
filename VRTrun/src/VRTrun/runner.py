import sys
import subprocess
import requests
import threading
import socket
import json
from typing import Optional, List, Any, cast, Union

__all__ = ["Runner", "RunnerServerPort"]

RunnerServerPort = 5002

RunnerArgs = dict[str, Any]


class Runner:
    host: str
    role : str
    statPath: str
    logPath: str
    exePath: str
    exeArgs : List[str]
    running : Any
    verbose = True
    runnerConfig : dict[str, dict[str, Union[str, bool]]] = {}
    mdnsWorkaround = True

    @classmethod
    def load_config(cls, filename : str) -> None:
        cls.runnerConfig = json.load(open(filename))

    def __init__(self, host: str, role : str, config: Optional[RunnerArgs] = None) -> None:
        self.host = host
        self.role = role
        self.running = None
        return
        if not config:
            config = self.runnerConfig.get(self.host)
            if not config:
                raise RuntimeError(f"Host key '{self.host}' not found in VRTstatistics configuration")
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

    def start(self, workdirname : str) -> None:
        url = f"http://{self.host}:{RunnerServerPort}/start"
        if self.verbose:
            print(f"+ POST {url} workdir={workdirname}")
        r = requests.post(url, json={'workdir' : workdirname})
        r.raise_for_status()
        
    def load_config_dir(self, configdir : str) -> None:
        pass

    def send_config(self) -> None:
        pass

    def receive_results(self) -> None:
        pass

    def get_log(self, filename : str) -> None:
        self.get_remotefile(self.logPath, filename)

    def get_stats(self, filename : str) -> None:
        self.get_remotefile(self.statPath, filename)

    def get_remotefile(self, remotepath : str, filename : str) -> None:
        self._get_remotefile_server(remotepath, filename)


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
        url = f"http://{self.host}:{RunnerServerPort}/putfile"
        if self.verbose:
            print(f"+ POST {url} filename={filename} data=...", file=sys.stderr)
        request_arg = {'filename' : filename, 'data' : data}
        r = requests.post(url, json=request_arg)
        rv = r.json()
        if self.verbose:
            print(f'- POST {url} -> {rv}')
        return rv['fullpath']

    def run(self) -> None:
        assert self.running == None
        self.running = threading.Thread(target=self._run_server_thread)
        self.running.start()

    def wait(self) -> int:
        assert self.running != None
        self.running.join()
        rv = self.status_code
        return rv

    def _run_server_thread(self):
        url = f"http://{self.host}:{RunnerServerPort}/run"
        if self.verbose:
            print(f"+ POST {url}", file=sys.stderr)
        response = requests.post(url)
        print(response.text)
        self.status_code = response.status_code if response.status_code != 200 else 0
