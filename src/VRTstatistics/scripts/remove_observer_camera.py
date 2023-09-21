import argparse
import math
import json
import sys

from collections import defaultdict
from functools import reduce
from operator import itemgetter
from typing import Optional, Dict, List, TypedDict, cast, TextIO


class LogEntry(TypedDict):
    component: str


class CameraLogEntry(LogEntry):
    px: float
    py: float
    pz: float


def get_cameras(data: List[LogEntry]) -> Dict[str, List[CameraLogEntry]]:
    """Returns all records which contain camera position information.

    Takes a JSON data structure containing logging information and filters it
    by records containing camera information. The records are returned as a
    dictionary grouped by camera ID.
    """
    def reduce_cameras(acc: Dict[str, List[CameraLogEntry]], record: LogEntry):
        if record["component"].startswith("PositionTracker#Camera"):
            acc[record["component"]].append(cast(CameraLogEntry, record))

        return acc

    return reduce(reduce_cameras, data, defaultdict(list))


def get_camera_movement_distance(camera_data: List[CameraLogEntry]) -> float:
    """Computes the total movement distance of a list of camera positions."""
    total_dist = 0.0

    for a, b in zip(camera_data, camera_data[1:]):
        # Compute distance between current and next position and sum it
        total_dist += math.sqrt(
            math.pow(a["px"] - b["px"], 2) +
            math.pow(a["py"] - b["py"], 2) +
            math.pow(a["pz"] - b["pz"], 2)
        )

    return total_dist


def get_observer_camera_id(cam_logs: Dict[str, List[CameraLogEntry]]) -> str:
    """Returns the ID of the observer camera.

    This function computes the distance each camera has moved. The camera that
    has moved the least is assumed to be the observer and its ID is returned.
    """
    distances = [
        (k, get_camera_movement_distance(v))
        for k, v in cam_logs.items()
    ]

    return sorted(distances, key=itemgetter(1))[0][0]


def filter_observer_data(data: List[LogEntry]) -> List[LogEntry]:
    """Filters out observer camera from a list of log entries.

    Takes a list of log entries and returns another list with all entries of
    what is determined to be the observer camera removed. The observer camera
    is assumed to be the camera that moved the least during the course of the
    session.
    """
    # Get camera records
    camera_data = get_cameras(data)
    # Get ID of camera which is most likely the observer
    observer_key = get_observer_camera_id(camera_data)

    # Filter out all records which contain observer camera information
    return [
        record for record in data
        if record["component"] != observer_key
    ]


def main(infile: TextIO, outfile: TextIO) -> None:
    # Parse input file at get all camera position records
    data = json.load(infile)

    # Filter out all records which contain observer camera information
    filtered_data = filter_observer_data(data)

    # If not output file name is given, print to stdout, otherwise write
    # to given output file name
    json.dump(filtered_data, outfile, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Filter observer camera from a log file."
    )
    parser.add_argument(
        "infile", default=None,
        help="Log file in JSON format"
    )
    parser.add_argument(
        "outfile", default=None, nargs="?",
        help="Filtered log file in JSON format (optional)"
    )
    args = parser.parse_args()

    infile = open(args.infile, "r")
    outfile = sys.stdout

    if args.outfile:
        outfile = open(args.outfile, "w")

    main(infile, outfile)
