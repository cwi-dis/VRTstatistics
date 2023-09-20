import math
import json
import sys

from collections import defaultdict
from functools import reduce
from operator import itemgetter
from typing import Optional, Dict, List, Any


def get_cameras(data) -> Dict[str, List[Any]]:
    """Returns all records which contain camera position information.

    Takes a JSON data structure containing logging information and filters it
    by records containing camera information. The records are returned as a
    dictionary grouped by camera ID.
    """
    def reduce_cameras(acc, record):
        if record["component"].startswith("PositionTracker#Camera"):
            acc[record["component"]].append(record)

        return acc

    return reduce(reduce_cameras, data, defaultdict(list))


def get_camera_movement(camera_data: List[Any]) -> float:
    """Computes the total movement distance of a list of camera positions."""
    total_dist = 0.0

    for i, record in enumerate(camera_data[:-1]):
        # Get next record
        next_record = camera_data[i+1]

        # Compute distance between current and next position and sum it
        total_dist += math.sqrt(
            math.pow(next_record["px"] - record["px"], 2) +
            math.pow(next_record["py"] - record["py"], 2) +
            math.pow(next_record["pz"] - record["pz"], 2)
        )

    return total_dist


def get_observer_camera(camera_data) -> str:
    """Returns the ID of the observer camera.

    This function computes the distance each camera has moved. The camera that
    has moved the least is assumed to be the observer and its ID is returned.
    """
    distances = [(k, get_camera_movement(v)) for k, v in camera_data.items()]
    return sorted(distances, key=itemgetter(1))[0][0]


def filter_observer_data(data: List[Any]) -> List[Any]:
    # Get camera records
    camera_data = get_cameras(data)
    # Get ID of camera which is most likely the observer
    observer_key = get_observer_camera(camera_data)

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
