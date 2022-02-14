import sys
import urllib.parse
import subprocess

from typing import Optional

__all__ = ["Runner", "RunnerConfig"]

RunnerArgs = dict
RunnerConfig = {
    "sap.local" : dict(
       statPath="Library/Application\\ Support/i2Cat/VRTogether/statistics.log",
       user="jack"
    ),
    "flauwte.local" : dict(
       statPath="Library/Application\\ Support/i2Cat/VRTogether/statistics.log",
       user="jack"
    ),
    "vrtiny.local" : dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log",
        user="vrtogether"
    ),
    "vrsmall.local" : dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log",
        user="vr-together"
    ),
    "vrbig.local" : dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log",
        user="vrtogether"
    ),
    "scallion.local" : dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log",
        user="vrtogether"
    ),
    "valkenburg-win10.local" : dict(
        statPath="AppData/LocalLow/i2Cat/VRTogether/statistics.log",
        user="dis"
    ),
}
    
class Runner:
    host : str
    user : str
    statPath : str
    verbose = True

    def __init__(self, url: str, config: Optional[RunnerArgs]=None) -> None:
        if ':' in url:
            parsed = urllib.parse.urlparse(self.url, scheme="ssh", allow_fragments=False)
            assert parsed.scheme == "ssh"
            assert parsed.hostname
            assert not parsed.port
            assert not parsed.password
            assert not parsed.query
            self.host = parsed.hostname
            self.user = parsed.username
        elif '@' in url:
            self.user, self.host = url.split('@')
        else:
            self.host = url
            self.user = ''
        if not config:
            config = RunnerConfig[self.host]
        if not self.user:
            self.user = config["user"]
        self.statPath = config["statPath"]

    def get_stats(self, filename):
        if self.user:
            sshPath = f'{self.user}@{self.host}:{self.statPath}'
        else:
            sshPath = f'{self.host}:{self.statPath}'
        cmd = ["scp", sshPath, filename]
        if self.verbose:
            print('+', ' '.join(cmd), file=sys.stderr)
        subprocess.run(cmd)
