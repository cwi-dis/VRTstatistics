import os
import json
import time
from typing import TextIO, List, Any, cast, Dict

__all__ = ["StatsFileParser"]

StatsRecord = Dict[str, Any]
StatsList = List[StatsRecord]

class StatsFileParser:
    filename: str
    data: StatsList

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.data = []

    def parse(self) -> StatsList:
        self.data = self._extractstats(open(self.filename))
        return self.data

    def save_json(self, statsfile: str) -> None:
        if not self.data:
            raise RuntimeError("No data")
        if os.path.isdir(statsfile):
            fn = os.path.splitext(os.path.basename(self.filename))[0]
            statsfile = os.path.join(statsfile, fn + ".json")
        json.dump(self.data, open(statsfile, "w"), indent="\t")

    def _extractstats(self, ifp: TextIO) -> StatsList:
        rv : StatsList = []
        localtime_epoch = None
        orchtime_epoch = None
        linenum = 0
        for line in ifp:
            linenum += 1
            line = line.strip()
            if not line.startswith("stats: "):
                continue
            line = line[7:]  # Remove the stats:
            entry = self._extractstats_single_new(line)
            #
            # See if we have info to allow conversion of timestamps already
            #
            if "orchestrator_ntptime_ms" in entry:
                orch_time = cast(float, entry["orchestrator_ntptime_ms"] / 1000.0)
                orch_gmtime = time.gmtime(orch_time)
                orch_midnight_gmtime = time.struct_time(
                    (
                        orch_gmtime.tm_year,
                        orch_gmtime.tm_mon,
                        orch_gmtime.tm_mday,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                    )
                )
                orch_midnight = time.mktime(orch_midnight_gmtime)
                localtime_epoch = orch_midnight
                orchtime_epoch = orch_time - entry["ts"]
            if localtime_epoch:
                entry["localtime"] = localtime_epoch + entry["ts"]
            if orchtime_epoch:
                entry["orchtime"] = orchtime_epoch + entry["ts"]
            rv.append(entry)
        return rv

    def _extractstats_single_new(self, line : str) -> StatsRecord:
        """Extract new-style statistics from a single line"""
        entry : StatsRecord = {}
        fields = line.split(",")
        for field in fields:
            field = field.strip()
            splitfield = field.split("=")
            k = splitfield[0]
            v = "=".join(splitfield[1:])
            # Try to convert v to natural value
            try:
                vi = int(v)
                v = vi
            except ValueError:
                try:
                    vf = float(v)
                    v = vf
                except ValueError:
                    pass
            entry[k] = v
        return entry

    def check(self) -> bool:
        ok = True
        startEntry = None
        stopEntry = None
        timeEntry = None
        for entry in self.data:
            if not entry["component"] == "OrchestratorController":
                continue
            if "starting" in entry:
                if startEntry:
                    print(f"{self.filename}: duplicate start of session")
                    ok = False
                startEntry = entry
            if "orchestrator_ntptime_ms" in entry:
                if timeEntry:
                    print(
                        f"{self.filename}: duplicate session time-synchronization entry"
                    )
                    ok = False
                timeEntry = entry
            if "stopping" in entry:
                if stopEntry:
                    print(f"{self.filename}: duplicate end of session")
                    ok = False
                stopEntry = entry
        if False and not startEntry:
            # Don't print this warning: the start entry is only printed for the initiator
            print(f"{self.filename}: warning: missing start of session ")
        if not timeEntry:
            print(f"{self.filename}: missing session time-synchronization entry")
            ok = False
        if not stopEntry:
            print(f"{self.filename}: warning: missing end of session")
        if (
            startEntry
            and stopEntry
            and startEntry["sessionId"] != stopEntry["sessionId"]
        ):
            print(f"{self.filename}: session different between start and stop")
            ok = False
        return ok
