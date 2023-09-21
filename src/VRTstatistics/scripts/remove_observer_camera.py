import math
import json
import sys

from collections import defaultdict
from functools import reduce
from operator import itemgetter
from typing import Optional, Dict, List, TypedDict, cast


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


def main(infile: str, outfile: Optional[str] = None) -> None:
    with open(infile, "r") as f:
        # Parse input file at get all camera position records
        data = json.load(f)

        # Filter out all records which contain observer camera information
        filtered_data = filter_observer_data(data)

        # If not output file name is given, print to stdout, otherwise write
        # to given output file name
        if outfile is None:
            print(json.dumps(filtered_data))
        else:
            with open(outfile, "w") as f:
                json.dump(filtered_data, f)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USAGE:", sys.argv[0], "input_json [output_json]")
        sys.exit(1)

    infile = sys.argv[1]
    outfile = None

    if len(sys.argv) == 3:
        outfile = sys.argv[2]

    main(infile, outfile)
