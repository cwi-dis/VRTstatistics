import sys
import urllib.parse
import subprocess

from typing import Optional

__all__ = ["Runner"]

RunnerArgs = dict
defaultRunnerConfig = {
    "sap.local": dict(
        statPath="Library/Application\\ Support/i2Cat/VRTogether/statistics.log",
        user="jack",
        exePath="/Users/jack/src/VRTogether/VRTApp-built-mmsys.app/Contents/MacOS/VRTogether",
        exeArgs=[]
    ),
    "flauwte.local": dict(
        statPath="Library/Application\\ Support/i2Cat/VRTogether/statistics.log",
        user="jack",
    ),
    "vrtiny.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", 
        user="vrtogether",
        exePath="c:/Users/VRTogether/VRTogether/VRTapp-built-mmsys/VRTogether.exe",
        exeArgs=["-batchmode"]
    ),
    "vrsmall.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", user="vr-together"
    ),
    "vrbig.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", user="vrtogether"
    ),
    "scallion.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", user="vrtogether"
    ),
    "valkenburg-win10.local": dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log", user="dis"
    ),
}


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
        self.exeArgs = config.get("exeArgs")

    def get_stats(self, filename):
        if self.user:
            scpPath = f"{self.user}@{self.host}:{self.statPath}"
        else:
            scpPath = f"{self.host}:{self.statPath}"
        cmd = ["scp", scpPath, filename]
        if self.verbose:
            print("+", " ".join(cmd), file=sys.stderr)
        subprocess.run(cmd)

    def run(self) -> subprocess.Popen:
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
        